import datetime
import logging
from typing import List, Sequence

from src import db
from src.config import Config
from src.migration_utils.google_sheets import (
    load_exercises_from_sheet,
    load_locations_from_sheet,
    load_sessions_from_sheet,
    load_workouts_from_sheet,
)
from src.models import Base
from src.schemas.go_heavier.migrations import (
    MigrationTable,
    RunMigrationRequest,
    RunMigrationResponse,
    TableMigrationResult,
)

logger = logging.getLogger(__name__)

cfg = Config()

# Each table is migrated after the ones it references.
MIGRATION_ORDER: Sequence[MigrationTable] = (
    MigrationTable.LOCATIONS,
    MigrationTable.EXERCISES,
    MigrationTable.SESSIONS,
    MigrationTable.WORKOUTS,
)


class MigrationConfigurationError(RuntimeError):
    """Raised when the migration cannot run because of missing configuration."""


class MigrationFailedError(RuntimeError):
    """Raised when a table could not be migrated.

    Carries the table name so that the router can log the whole failure in one
    line, rather than each layer logging its own half of it.
    """


def _load_rows(table: MigrationTable, request: RunMigrationRequest) -> List[Base]:
    if table == MigrationTable.LOCATIONS:
        return load_locations_from_sheet(cfg=cfg)
    if table == MigrationTable.EXERCISES:
        return load_exercises_from_sheet(cfg=cfg)

    # Sessions and sets come from the same sheet and take the same narrowing,
    # so that a set is never loaded without the session it belongs to.
    load = (
        load_sessions_from_sheet
        if table == MigrationTable.SESSIONS
        else load_workouts_from_sheet
    )
    return load(
        cfg=cfg,
        range_start=request.workouts_row_start or 0,
        range_end=request.workouts_row_end,
        after=request.workouts_after,
        before=request.workouts_before,
    )


def run_migration(request: RunMigrationRequest) -> RunMigrationResponse:
    """Load the Google Sheet into the database, upserting each requested table."""
    if cfg.google_service_account_filepath is None:
        raise MigrationConfigurationError("Missing google service account file")

    results: List[TableMigrationResult] = []
    for table in MIGRATION_ORDER:
        if table not in request.tables:
            continue

        try:
            rows = _load_rows(table=table, request=request)
            logger.info(f"Loaded {len(rows)} {table.value} from the sheet")

            if request.dry_run:
                results.append(
                    TableMigrationResult(table=table, rows=len(rows), written=0)
                )
                continue

            now = datetime.datetime.now(tz=datetime.timezone.utc)
            for row in rows:
                row.updated_at = now
                db.session.merge(row)
            db.session.commit()
        except Exception as e:
            # The session is shared across requests, so it must not be left dirty
            db.session.rollback()
            raise MigrationFailedError(f"could not migrate {table.value}: {e}") from e

        results.append(
            TableMigrationResult(table=table, rows=len(rows), written=len(rows))
        )

    return RunMigrationResponse(dry_run=request.dry_run, results=results)
