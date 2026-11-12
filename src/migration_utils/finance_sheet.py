"""Loading the finance spreadsheet into models.

The whole spreadsheet is read in two requests, one for its formatted values
and one for its unformatted ones, since Google limits how many reads a minute
a service account can make and there's a tab per month.
"""

import dataclasses
import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

import gspread
import pendulum
from gspread.utils import absolute_range_name, rowcol_to_a1

from src.config import Config
from src.migration_utils.finance_categories import CATEGORY_GROUPS, category_id_for
from src.migration_utils.finance_rows import (
    ID_HEADER,
    SheetBudget,
    SheetSpend,
    budget_id_for,
    id_column,
    is_month_tab,
    merchant_id_for,
    merchant_key,
    parse_breakdown_tab,
    parse_month_tab,
    payment_method_id_for,
    payment_method_kind,
)
from src.models.finance import Budget, Category, Merchant, PaymentMethod, Transaction

logger = logging.getLogger(__name__)

MERCHANTS_TAB = "Merchants"


@dataclasses.dataclass
class FinanceWorkbook:
    spreadsheet: gspread.Spreadsheet
    # Each month's tab as (formatted, unformatted) rows
    months: Dict[str, tuple]
    breakdowns: Dict[str, List[List[Any]]]
    merchants: List[str]
    column_counts: Dict[str, int]


def _open(cfg: Config) -> gspread.Spreadsheet:
    client: gspread.Client = gspread.service_account(
        filename=cfg.google_service_account_filepath
    )
    return client.open_by_key(cfg.FINANCE_SPREADSHEET_ID)


def _batch_get(
    spreadsheet: gspread.Spreadsheet, tabs: List[str], render: str
) -> Dict[str, List[List[Any]]]:
    response = spreadsheet.values_batch_get(
        [absolute_range_name(tab) for tab in tabs],
        params={"valueRenderOption": render},
    )
    return {
        tab: value_range.get("values", [])
        for tab, value_range in zip(tabs, response["valueRanges"])
    }


def read_workbook(cfg: Config) -> FinanceWorkbook:
    spreadsheet = _open(cfg)
    worksheets = spreadsheet.worksheets()
    titles = [worksheet.title for worksheet in worksheets]

    months = [title for title in titles if is_month_tab(title)]
    breakdowns = [title for title in titles if title.endswith("-Breakdown")]
    tabs = months + breakdowns + ([MERCHANTS_TAB] if MERCHANTS_TAB in titles else [])

    formatted = _batch_get(spreadsheet, tabs, "FORMATTED_VALUE")
    raw = _batch_get(spreadsheet, tabs, "UNFORMATTED_VALUE")

    return FinanceWorkbook(
        spreadsheet=spreadsheet,
        months={tab: (formatted[tab], raw[tab]) for tab in months},
        breakdowns={tab: raw[tab] for tab in breakdowns},
        merchants=[
            row[0] for row in formatted.get(MERCHANTS_TAB, []) if row and row[0]
        ],
        column_counts={
            worksheet.title: worksheet.col_count for worksheet in worksheets
        },
    )


def read_spends(workbook: FinanceWorkbook) -> List[SheetSpend]:
    return [
        spend
        for tab, (formatted, raw) in workbook.months.items()
        for spend in parse_month_tab(tab, formatted, raw)
    ]


def read_budgets(workbook: FinanceWorkbook) -> List[SheetBudget]:
    return [
        budget
        for tab, raw in workbook.breakdowns.items()
        for budget in parse_breakdown_tab(tab, raw)
    ]


def assign_missing_ids(
    workbook: FinanceWorkbook, spends: List[SheetSpend], write: bool
) -> int:
    """Give every spend without an id a new one, returning how many there were.

    With ``write`` they're also written to the tab's ID column, adding the
    column if it isn't there yet, so the next import finds the same ids. All
    of them go in one request.
    """
    missing = [spend for spend in spends if spend.id is None]
    for spend in missing:
        spend.id = uuid.uuid4()
    if not write or not missing:
        return len(missing)

    updates: List[Dict[str, Any]] = []
    for tab in sorted({spend.tab for spend in missing}):
        formatted, _ = workbook.months[tab]
        header = formatted[0] if formatted else []
        column = id_column(header) + 1

        if column > workbook.column_counts.get(tab, column):
            workbook.spreadsheet.worksheet(tab).add_cols(
                column - workbook.column_counts[tab]
            )
            workbook.column_counts[tab] = column

        if ID_HEADER not in header:
            updates.append(
                {
                    "range": absolute_range_name(tab, rowcol_to_a1(1, column)),
                    "values": [[ID_HEADER]],
                }
            )
        updates.extend(
            {
                "range": absolute_range_name(
                    tab, rowcol_to_a1(spend.sheet_row, column)
                ),
                "values": [[str(spend.id)]],
            }
            for spend in missing
            if spend.tab == tab
        )

    workbook.spreadsheet.values_batch_update(
        {"valueInputOption": "RAW", "data": updates}
    )
    logger.info(f"Wrote {len(missing)} new ids to the finance sheet")
    return len(missing)


def build_categories() -> List[Category]:
    now = pendulum.now("UTC")
    return [
        Category(
            id=category_id_for(name),
            group=group,
            name=name,
            created_at=now,
            updated_at=now,
        )
        for name, group in CATEGORY_GROUPS.items()
    ]


def build_payment_methods(spends: List[SheetSpend]) -> List[PaymentMethod]:
    now = pendulum.now("UTC")
    names = sorted({spend.payment_method for spend in spends})
    return [
        PaymentMethod(
            id=payment_method_id_for(name),
            name=name,
            kind=payment_method_kind(name).value,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        for name in names
    ]


def build_merchants(
    workbook: FinanceWorkbook, spends: List[SheetSpend]
) -> List[Merchant]:
    """Every merchant in the Merchants tab, and any spent with that isn't.

    Spellings differing only in case or spacing are one merchant, named the
    way the Merchants tab names it, or else as it's first spelt.
    """
    names: Dict[str, str] = {}
    for name in workbook.merchants + [spend.merchant for spend in spends]:
        if name:
            names.setdefault(merchant_key(name), " ".join(name.split()))

    now = pendulum.now("UTC")
    return [
        Merchant(id=merchant_id_for(name), name=name, created_at=now, updated_at=now)
        for name in names.values()
    ]


def build_transactions(
    spends: List[SheetSpend],
    after: Optional[datetime.date] = None,
    before: Optional[datetime.date] = None,
) -> List[Transaction]:
    now = pendulum.now("UTC")
    return [
        Transaction(
            id=spend.id,
            spent_on=spend.spent_on,
            amount_gbp=spend.amount_gbp,
            original_amount=spend.original_amount,
            original_currency=spend.original_currency,
            payment_method_id=payment_method_id_for(spend.payment_method),
            merchant_id=merchant_id_for(spend.merchant) if spend.merchant else None,
            category_id=category_id_for(spend.category) if spend.category else None,
            description=spend.description,
            is_necessary=spend.is_necessary,
            is_recurring=spend.is_recurring,
            with_partner=spend.with_partner,
            time_of_day=spend.time_of_day.value if spend.time_of_day else None,
            created_at=now,
            updated_at=now,
        )
        for spend in spends
        if (after is None or spend.spent_on >= after)
        and (before is None or spend.spent_on <= before)
    ]


def build_budgets(budgets: List[SheetBudget]) -> List[Budget]:
    now = pendulum.now("UTC")
    return [
        Budget(
            id=budget_id_for(budget.category, budget.year),
            category_id=category_id_for(budget.category),
            year=budget.year,
            monthly_target_gbp=budget.monthly_target_gbp,
            rationale=budget.rationale,
            created_at=now,
            updated_at=now,
        )
        for budget in budgets
    ]
