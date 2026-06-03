"""add location data

Revision ID: ac52a7b2cd78
Revises: 1834e54859ea
Create Date: 2026-06-02 22:28:11.759058

"""

import datetime
from typing import Sequence, Union

from src import db
from src.config import Config
from src.migration_utils.google_sheets import load_locations_from_sheet
from src.models.go_heavier import Location, Workout

# revision identifiers, used by Alembic.
revision: str = "ac52a7b2cd78"
down_revision: Union[str, Sequence[str], None] = "1834e54859ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

cfg = Config()
start = datetime.datetime.fromtimestamp(0).replace(tzinfo=datetime.timezone.utc)
end = datetime.datetime(2026, 6, 2).replace(tzinfo=datetime.timezone.utc)


def upgrade() -> None:
    if cfg.google_service_account_filepath is None:
        raise RuntimeError("Missing google service account file")

    locations = load_locations_from_sheet(cfg=cfg)
    for filtered_location in filter(
        lambda location: start <= location.created_at <= end, locations
    ):
        print("adding/updating {}".format(filtered_location))
        # Update updated_at to now for merge operations
        filtered_location.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.session.merge(filtered_location)
    db.session.commit()


def downgrade() -> None:
    """Downgrade schema."""
    if cfg.google_service_account_filepath is None:
        raise RuntimeError("Missing google service account file")

    locations = load_locations_from_sheet(cfg=cfg)
    location_ids = [
        location.id for location in locations if start <= location.created_at <= end
    ]

    if location_ids:
        # First delete any workouts that reference these locations
        workout_count = (
            db.session.query(Workout)
            .filter(Workout.location_id.in_(location_ids))
            .delete(synchronize_session=False)
        )
        if workout_count > 0:
            print(f"Deleted {workout_count} workouts referencing these locations")

        # Then delete the locations
        db.session.query(Location).filter(Location.id.in_(location_ids)).delete(
            synchronize_session=False
        )
        db.session.commit()
        print(f"Deleted {len(location_ids)} locations")
