"""add workout data

Revision ID: 9b3a6dc93a77
Revises: c1e10239e50d
Create Date: 2026-06-03 01:03:24.443041

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "9b3a6dc93a77"
down_revision: Union[str, Sequence[str], None] = "c1e10239e50d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Kept as a no-op.

    This loaded the workouts out of the Google Sheet using the model classes as they
    were at the time. Those have moved on, so replaying it against the schema
    of this revision fails, which broke `alembic upgrade head` on any new
    database. The rows it added are long since in the databases that need
    them, and the same load is available on demand through
    POST /go-heavier/migrations.
    """


def downgrade() -> None:
    """Kept as a no-op, see upgrade."""
