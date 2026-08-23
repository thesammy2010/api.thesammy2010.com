"""add exercise data

Revision ID: c1e10239e50d
Revises: ac52a7b2cd78
Create Date: 2026-06-03 00:50:19.300413

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "c1e10239e50d"
down_revision: Union[str, Sequence[str], None] = "ac52a7b2cd78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Kept as a no-op.

    This loaded the exercises out of the Google Sheet using the model classes as they
    were at the time. Those have moved on, so replaying it against the schema
    of this revision fails, which broke `alembic upgrade head` on any new
    database. The rows it added are long since in the databases that need
    them, and the same load is available on demand through
    POST /go-heavier/migrations.
    """


def downgrade() -> None:
    """Kept as a no-op, see upgrade."""
