"""add exercise data

Revision ID: c1e10239e50d
Revises: ac52a7b2cd78
Create Date: 2026-06-03 00:50:19.300413

"""

import datetime
from typing import Sequence, Union

from src import db
from src.config import Config
from src.migration_utils.google_sheets import load_exercises_from_sheet
from src.models.go_heavier import Exercise, Workout

# revision identifiers, used by Alembic.
revision: str = "c1e10239e50d"
down_revision: Union[str, Sequence[str], None] = "ac52a7b2cd78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


cfg = Config()
start = datetime.datetime.fromtimestamp(0).replace(tzinfo=datetime.timezone.utc)
end = datetime.datetime(2026, 6, 2).replace(tzinfo=datetime.timezone.utc)


def upgrade() -> None:
    if cfg.google_service_account_filepath is None:
        raise RuntimeError("Missing google service account file")

    exercises = load_exercises_from_sheet(cfg=cfg)
    for filtered_exercise in filter(
        lambda exercise: start <= exercise.created_at <= end, exercises
    ):
        print("adding/updating {}".format(filtered_exercise))
        # Update updated_at to now for merge operations
        filtered_exercise.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.session.merge(filtered_exercise)
    db.session.commit()


def downgrade() -> None:
    """Downgrade schema."""
    if cfg.google_service_account_filepath is None:
        raise RuntimeError("Missing google service account file")

    exercises = load_exercises_from_sheet(cfg=cfg)
    exercise_ids = [
        exercise.id for exercise in exercises if start <= exercise.created_at <= end
    ]

    if exercise_ids:
        # First delete any workouts that reference these exercises
        workout_count = (
            db.session.query(Workout)
            .filter(Workout.exercise_id.in_(exercise_ids))
            .delete(synchronize_session=False)
        )
        if workout_count > 0:
            print(f"Deleted {workout_count} workouts referencing these exercises")

        # Then delete the exercises
        db.session.query(Exercise).filter(Exercise.id.in_(exercise_ids)).delete(
            synchronize_session=False
        )
        db.session.commit()
        print(f"Deleted {len(exercise_ids)} exercises")
