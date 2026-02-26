"""go_heavier: add workout data

Revision ID: 77fec11e24db
Revises: 2cfd9b746fcc
Create Date: 2026-02-21 00:42:40.925372

"""

import datetime
from typing import List, Sequence, Union

from alembic import op

from src import db
from src.config import Config
from src.migration_utils.google_sheets import (
    get_workout_from_sheet,
)
from src.models.go_heavier import Workout

# revision identifiers, used by Alembic.
revision: str = "77fec11e24db"
down_revision: Union[str, Sequence[str], None] = "2cfd9b746fcc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

cfg = Config()
start = datetime.datetime.fromtimestamp(0).replace(tzinfo=datetime.timezone.utc)
end = datetime.datetime(2025, 8, 13).replace(tzinfo=datetime.timezone.utc)


def upgrade() -> None:
    if cfg.google_service_account_filepath is None:
        raise RuntimeError("Missing google service account file")

    workouts: List[Workout] = get_workout_from_sheet(cfg=cfg)

    for filtered_workout in filter(
        lambda workout: start <= workout.workout_time <= end, workouts
    ):
        print("adding {}".format(filtered_workout))
        db.session.add(filtered_workout)
        db.session.commit()


def downgrade() -> None:
    query: str = "DELETE FROM {} WHERE {} BETWEEN '{}' AND '{}'".format(
        Workout.__tablename__, Workout.workout_time.property.key, start, end
    )
    op.execute(query)
