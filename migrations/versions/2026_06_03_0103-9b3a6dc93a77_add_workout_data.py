"""add workout data

Revision ID: 9b3a6dc93a77
Revises: c1e10239e50d
Create Date: 2026-06-03 01:03:24.443041

"""

import datetime
from typing import Sequence, Union

from src import db
from src.config import Config
from src.migration_utils.google_sheets import load_workouts_from_sheet
from src.models.go_heavier import Workout

# revision identifiers, used by Alembic.
revision: str = "9b3a6dc93a77"
down_revision: Union[str, Sequence[str], None] = "c1e10239e50d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


cfg = Config()
start = datetime.datetime.fromtimestamp(0).replace(tzinfo=datetime.timezone.utc)
end = datetime.datetime(2026, 6, 2).replace(tzinfo=datetime.timezone.utc)
range_start = 0
range_end = 815


def upgrade() -> None:
    if cfg.google_service_account_filepath is None:
        raise RuntimeError("Missing google service account file")

    workouts = load_workouts_from_sheet(
        cfg=cfg, range_start=range_start, range_end=range_end
    )
    for filtered_workout in filter(
        lambda workout: start <= workout.workout_time <= end, workouts
    ):
        print("adding/updating {}".format(filtered_workout))
        # Update updated_at to now for merge operations
        filtered_workout.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.session.merge(filtered_workout)
    db.session.commit()


def downgrade() -> None:
    """Downgrade schema."""
    if cfg.google_service_account_filepath is None:
        raise RuntimeError("Missing google service account file")

    workouts = load_workouts_from_sheet(
        cfg=cfg, range_start=range_start, range_end=range_end
    )
    workout_ids = [
        workout.id for workout in workouts if start <= workout.created_at <= end
    ]

    if workout_ids:
        db.session.query(Workout).filter(Workout.id.in_(workout_ids)).delete(
            synchronize_session=False
        )
        db.session.commit()
        print(f"Deleted {len(workout_ids)} workouts")
