import logging

from fastapi import APIRouter, HTTPException

from src.resolvers.go_heavier import migrations
from src.resolvers.go_heavier.migrations import MigrationConfigurationError
from src.schemas.go_heavier.migrations import (
    RunMigrationRequest,
    RunMigrationResponse,
)

router = APIRouter(prefix="/go-heavier", tags=["migrations"])


@router.post("/migrations", response_model=RunMigrationResponse)
def run_migration(request: RunMigrationRequest) -> RunMigrationResponse:
    try:
        return migrations.run_migration(request=request)
    except MigrationConfigurationError as e:
        logging.error(f"Cannot run migration: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logging.error(f"Error running migration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
