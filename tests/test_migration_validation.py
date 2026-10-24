"""Tests for validating the rows loaded from the sheet before they are written.

The loaders are replaced so that these run without the sheet, and every run is
a dry run or is rejected before writing, so they need no database either.
"""

import datetime
import uuid
from types import SimpleNamespace

import pytest

from src.models.go_heavier import Workout
from src.resolvers.go_heavier import migrations
from src.schemas.go_heavier.migrations import MigrationTable, RunMigrationRequest

SESSION = uuid.UUID("0b9a3a51-6e0a-4f25-bd52-4dd8f3a3e0aa")
BENCH = uuid.UUID("55c2fa3a-789b-4431-a207-018636eec66c")


def workout(repetitions: int = 10, index: int = 1) -> Workout:
    return Workout(
        id=uuid.uuid4(),
        session_id=SESSION,
        exercise_id=BENCH,
        index=index,
        repetitions=repetitions,
        weight_kg=50.0,
        created_at=datetime.datetime(2026, 8, 7, tzinfo=datetime.timezone.utc),
    )


@pytest.fixture
def sheet(monkeypatch):
    """Install fake loaded rows, returning a setter for the workouts."""
    monkeypatch.setattr(
        migrations, "cfg", SimpleNamespace(google_service_account_filepath="sa.json")
    )

    def set_workouts(*rows: Workout):
        monkeypatch.setattr(migrations, "_load_rows", lambda table, request: list(rows))

    return set_workouts


def run(dry_run: bool = True):
    return migrations.run_migration(
        RunMigrationRequest(tables=[MigrationTable.WORKOUTS], dry_run=dry_run)
    )


class TestMigrationValidation:
    """Test that the sheet cannot load a row the API would reject."""

    def test_valid_rows_pass(self, sheet):
        sheet(workout(), workout(index=2))

        (result,) = run().results

        assert result.rows == 2

    def test_a_set_with_no_repetitions_is_rejected(self, sheet):
        bad = workout(repetitions=0)
        sheet(workout(), bad)

        with pytest.raises(migrations.MigrationValidationError) as e:
            run()

        assert e.value.table == MigrationTable.WORKOUTS
        (error,) = e.value.errors
        assert str(bad.id) in error
        assert "repetitions" in error

    def test_every_invalid_row_is_reported(self, sheet):
        sheet(workout(repetitions=0), workout(index=0), workout())

        with pytest.raises(migrations.MigrationValidationError) as e:
            run()

        assert len(e.value.errors) == 2

    def test_a_real_run_is_rejected_before_writing(self, sheet, monkeypatch):
        sheet(workout(repetitions=0))
        merged = []
        monkeypatch.setattr(migrations.db.session, "merge", merged.append)

        with pytest.raises(migrations.MigrationValidationError):
            run(dry_run=False)

        assert merged == []
