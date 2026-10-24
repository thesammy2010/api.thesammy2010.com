import logging

from fastapi import APIRouter, Depends, HTTPException

from src.resolvers.go_heavier import migrations
from src.resolvers.go_heavier.migrations import (
    MigrationConfigurationError,
    MigrationValidationError,
)
from src.resolvers.users import require_admin
from src.schemas.go_heavier.migrations import (
    RunMigrationRequest,
    RunMigrationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/go-heavier", tags=["migrations"])


@router.post(
    "/migrations",
    response_model=RunMigrationResponse,
    dependencies=[Depends(require_admin)],
)
def run_migration(request: RunMigrationRequest) -> RunMigrationResponse:
    """Upserts rows from the Go Heavier Google Sheet into the database.

    Tables are always migrated in dependency order (locations, exercises,
    sessions, then workouts) regardless of the order given in `tables`.
    503 if GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 / GOOGLE_SPREADSHEET_ID
    aren't configured. 422 if any row fails the validation the API applies
    when that resource is written, in which case nothing from that table or
    any after it is written.
    """
    try:
        return migrations.run_migration(request=request)
    except MigrationConfigurationError as e:
        logger.error(f"Cannot run migration: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except MigrationValidationError as e:
        logger.error(f"Migration rejected: {e}")
        raise HTTPException(
            status_code=422,
            detail={"table": e.table.value, "errors": e.errors},
        )
    except Exception as e:
        logger.error(f"Error running migration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
