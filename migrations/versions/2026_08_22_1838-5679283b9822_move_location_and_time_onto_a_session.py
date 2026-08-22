"""move location and time onto a session

Revision ID: 5679283b9822
Revises: 4c0deee26f71
Create Date: 2026-08-22 18:38:16.947942

"""

import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from src.migration_utils.session_ids import session_id_for

# revision identifiers, used by Alembic.
revision: str = "5679283b9822"
down_revision: Union[str, Sequence[str], None] = "4c0deee26f71"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Give a session its own row, rather than repeating it on every set."""
    op.create_table(
        "sessions",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("workout_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            name=op.f("fk_sessions_location_id_locations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        sa.UniqueConstraint(
            "location_id", "workout_time", name=op.f("uq_sessions_location_id")
        ),
    )
    op.add_column("workouts", sa.Column("session_id", sa.Uuid(), nullable=True))

    _backfill_sessions()

    op.alter_column("workouts", "session_id", nullable=False)
    op.create_foreign_key(
        op.f("fk_workouts_session_id_sessions"),
        "workouts",
        "sessions",
        ["session_id"],
        ["id"],
    )
    op.drop_constraint(op.f("fk_workouts_location_id_locations"), "workouts")
    op.drop_column("workouts", "location_id")
    op.drop_column("workouts", "workout_time")
    # Never populated in any environment
    op.drop_column("workouts", "exercise_index")


def _backfill_sessions() -> None:
    """Create one session per location and time, and point the sets at it.

    The ids are derived rather than random so that re-running the sheet load
    merges onto these same rows instead of inserting duplicates.
    """
    connection = op.get_bind()
    existing = connection.execute(
        sa.text(
            "select distinct location_id, workout_time from workouts "
            "order by workout_time"
        )
    ).all()

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    for location_id, workout_time in existing:
        session_id = session_id_for(location_id=location_id, workout_time=workout_time)
        connection.execute(
            sa.text(
                "insert into sessions "
                "(id, location_id, workout_time, created_at, updated_at) "
                "values (:id, :location_id, :workout_time, :now, :now)"
            ),
            {
                "id": session_id,
                "location_id": location_id,
                "workout_time": workout_time,
                "now": now,
            },
        )
        connection.execute(
            sa.text(
                "update workouts set session_id = :id "
                "where location_id = :location_id and workout_time = :workout_time"
            ),
            {
                "id": session_id,
                "location_id": location_id,
                "workout_time": workout_time,
            },
        )

    print(f"Created {len(existing)} sessions")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("workouts", sa.Column("exercise_index", sa.Integer(), nullable=True))
    op.add_column("workouts", sa.Column("location_id", sa.Uuid(), nullable=True))
    op.add_column(
        "workouts", sa.Column("workout_time", sa.DateTime(timezone=True), nullable=True)
    )
    op.execute(
        "update workouts set location_id = sessions.location_id, "
        "workout_time = sessions.workout_time "
        "from sessions where sessions.id = workouts.session_id"
    )
    op.alter_column("workouts", "location_id", nullable=False)
    op.alter_column("workouts", "workout_time", nullable=False)
    op.create_foreign_key(
        op.f("fk_workouts_location_id_locations"),
        "workouts",
        "locations",
        ["location_id"],
        ["id"],
    )

    op.drop_constraint(op.f("fk_workouts_session_id_sessions"), "workouts")
    op.drop_column("workouts", "session_id")
    op.drop_table("sessions")
