import datetime
import logging
from typing import Dict, List, Type

import pendulum
from pydantic import BaseModel, ValidationError

from src import db
from src.config import Config
from src.migration_utils import finance_sheet
from src.models import Base
from src.models.finance import Transaction
from src.resolvers.go_heavier.migrations import MigrationConfigurationError
from src.schemas.finance.budgets import PutBudgetRequest
from src.schemas.finance.merchants import MerchantRequest
from src.schemas.finance.migrations import (
    FinanceTable,
    FinanceTableResult,
    RunFinanceMigrationRequest,
    RunFinanceMigrationResponse,
)
from src.schemas.finance.payment_methods import PaymentMethodRequest
from src.schemas.finance.transactions import TransactionRequest

logger = logging.getLogger(__name__)

cfg = Config()

# The schema the API validates each resource against when it is written, so
# that the sheet cannot load a row the API would have rejected. Categories
# come from the code rather than the sheet, so have nothing to check.
ROW_SCHEMAS: Dict[FinanceTable, Type[BaseModel]] = {
    FinanceTable.PAYMENT_METHODS: PaymentMethodRequest,
    FinanceTable.MERCHANTS: MerchantRequest,
    FinanceTable.TRANSACTIONS: TransactionRequest,
    FinanceTable.BUDGETS: PutBudgetRequest,
}


class FinanceMigrationValidationError(ValueError):
    """Raised when rows from the sheet fail the API's validation."""

    def __init__(self, table: FinanceTable, errors: List[str]):
        self.table = table
        self.errors = errors
        super().__init__(
            f"{len(errors)} {table.value} failed validation: " + "; ".join(errors)
        )


def _validate_rows(table: FinanceTable, rows: List[Base]) -> None:
    """Check every row before any is written, reporting all the failures at once."""
    schema = ROW_SCHEMAS.get(table)
    if schema is None:
        return
    errors: List[str] = []
    for row in rows:
        try:
            schema.model_validate(row)
        except ValidationError as e:
            problems = ", ".join(
                f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                for err in e.errors()
            )
            errors.append(f"{row.id} ({problems})")
    if errors:
        raise FinanceMigrationValidationError(table=table, errors=errors)


def _validate_relations(transactions: List[Transaction]) -> None:
    """Check every related spend refers to one that exists and belongs to none.

    The one it refers to may be in this import or already in the database,
    such as when the import is narrowed by date.
    """
    by_id = {row.id: row for row in transactions}
    missing = {
        row.related_to_id
        for row in transactions
        if row.related_to_id is not None and row.related_to_id not in by_id
    }
    elsewhere = (
        dict(
            db.session.query(Transaction.id, Transaction.related_to_id)
            .filter(Transaction.id.in_(missing))
            .all()
        )
        if missing
        else {}
    )

    errors: List[str] = []
    for row in transactions:
        if row.related_to_id is None:
            continue
        if row.related_to_id == row.id:
            errors.append(f"{row.id} (related to itself)")
        elif row.related_to_id in by_id:
            if by_id[row.related_to_id].related_to_id is not None:
                errors.append(
                    f"{row.id} (related to {row.related_to_id}, which is itself "
                    "related to another)"
                )
        elif row.related_to_id not in elsewhere:
            errors.append(
                f"{row.id} (related to {row.related_to_id}, which isn't in the "
                "sheet's imported spends or the database)"
            )
        elif elsewhere[row.related_to_id] is not None:
            errors.append(
                f"{row.id} (related to {row.related_to_id}, which is itself "
                "related to another)"
            )
    if errors:
        raise FinanceMigrationValidationError(
            table=FinanceTable.TRANSACTIONS, errors=errors
        )


def run_migration(request: RunFinanceMigrationRequest) -> RunFinanceMigrationResponse:
    """Load the finance sheet into the database, upserting every table.

    Every spend is given an id in the sheet first, including ones outside the
    requested dates, so the sheet never has a spend without one for long.
    Spends removed from the sheet are not removed from the database.
    """
    if cfg.google_service_account_filepath is None:
        raise MigrationConfigurationError("Missing google service account file")
    if not cfg.FINANCE_SPREADSHEET_ID:
        raise MigrationConfigurationError("FINANCE_SPREADSHEET_ID is not set")

    workbook = finance_sheet.read_workbook(cfg=cfg)
    spends = finance_sheet.read_spends(workbook)
    ids_assigned = finance_sheet.assign_missing_ids(
        workbook, spends, write=not request.dry_run
    )

    # Anything dated after today is the sheet's estimate of a spend still to
    # come, which may yet change or not happen at all
    today = pendulum.today("Europe/London").date()
    before = min(request.before, today) if request.before else today
    transactions = finance_sheet.build_transactions(
        spends, after=request.after, before=before
    )

    # Each table is migrated after the ones it references
    tables: Dict[FinanceTable, List[Base]] = {
        FinanceTable.CATEGORIES: finance_sheet.build_categories(),
        FinanceTable.PAYMENT_METHODS: finance_sheet.build_payment_methods(spends),
        FinanceTable.MERCHANTS: finance_sheet.build_merchants(workbook, spends),
        FinanceTable.TRANSACTIONS: transactions,
        FinanceTable.BUDGETS: finance_sheet.build_budgets(
            finance_sheet.read_budgets(workbook)
        ),
    }
    for table, rows in tables.items():
        _validate_rows(table, rows)
    _validate_relations(transactions)

    results: List[FinanceTableResult] = []
    try:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        for table, rows in tables.items():
            logger.info(f"Loaded {len(rows)} {table.value} from the finance sheet")
            if not request.dry_run:
                for row in rows:
                    row.updated_at = now
                    db.session.merge(row)
                # Flushed per table so each one's foreign keys can see the
                # rows it refers to
                db.session.flush()
            results.append(
                FinanceTableResult(
                    table=table,
                    rows=len(rows),
                    written=0 if request.dry_run else len(rows),
                )
            )
        if not request.dry_run:
            db.session.commit()
    except Exception:
        # The session is shared across requests, so it must not be left dirty
        db.session.rollback()
        raise

    return RunFinanceMigrationResponse(
        dry_run=request.dry_run,
        ids_assigned=ids_assigned,
        uncategorised=sum(1 for row in transactions if row.category_id is None),
        results=results,
    )
