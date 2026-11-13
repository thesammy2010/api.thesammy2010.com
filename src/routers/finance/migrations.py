import logging

from fastapi import APIRouter, Depends, HTTPException

from src.resolvers.finance import migrations
from src.resolvers.finance.migrations import FinanceMigrationValidationError
from src.resolvers.go_heavier.migrations import MigrationConfigurationError
from src.resolvers.users import require_admin
from src.schemas.finance.migrations import (
    RunFinanceMigrationRequest,
    RunFinanceMigrationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/finance",
    tags=["migrations"],
    dependencies=[Depends(require_admin)],
)


@router.post("/migrations", response_model=RunFinanceMigrationResponse)
def run_migration(request: RunFinanceMigrationRequest) -> RunFinanceMigrationResponse:
    """Upserts the finance Google Sheet into the database.

    Any spend in the sheet without an id is given one, written into its
    tab's ID column, so importing again updates it rather than adding it
    twice. Spends dated after today aren't imported. The sheet's older
    categories are mapped onto the current ones. 503 if the service account
    or FINANCE_SPREADSHEET_ID isn't configured. 422 if any row fails the
    validation the API applies when that resource is written, in which case
    nothing is written to the database (though new ids are still written to
    the sheet).
    """
    try:
        return migrations.run_migration(request=request)
    except MigrationConfigurationError as e:
        logger.error(f"Cannot run finance migration: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except FinanceMigrationValidationError as e:
        logger.error(f"Finance migration rejected: {e}")
        raise HTTPException(
            status_code=422,
            detail={"table": e.table.value, "errors": e.errors},
        )
    except Exception as e:
        logger.error(f"Error running finance migration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
