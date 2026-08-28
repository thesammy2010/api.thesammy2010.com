import logging

from fastapi import APIRouter, Depends, HTTPException

from src.resolvers.go_heavier import migrations
from src.resolvers.go_heavier.migrations import MigrationConfigurationError
from src.resolvers.users import require_editor
from src.schemas.go_heavier.migrations import (
    RunMigrationRequest,
    RunMigrationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/go-heavier", tags=["migrations"])


@router.post(
    "/migrations",
    response_model=RunMigrationResponse,
    dependencies=[Depends(require_editor)],
)
def run_migration(request: RunMigrationRequest) -> RunMigrationResponse:
    """Upserts rows from the Go Heavier Google Sheet into the database.

    Tables are always migrated in dependency order (locations, exercises,
    sessions, then workouts) regardless of the order given in `tables`.
    503 if GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 / GOOGLE_SPREADSHEET_ID
    aren't configured.
    """
    try:
        return migrations.run_migration(request=request)
    except MigrationConfigurationError as e:
        logger.error(f"Cannot run migration: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error running migration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
