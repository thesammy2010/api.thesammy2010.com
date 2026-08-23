"""add location data

Revision ID: ac52a7b2cd78
Revises: 1834e54859ea
Create Date: 2026-06-02 22:28:11.759058

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "ac52a7b2cd78"
down_revision: Union[str, Sequence[str], None] = "1834e54859ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Kept as a no-op.

    This loaded the locations out of the Google Sheet using the model classes as they
    were at the time. Those have moved on, so replaying it against the schema
    of this revision fails, which broke `alembic upgrade head` on any new
    database. The rows it added are long since in the databases that need
    them, and the same load is available on demand through
    POST /go-heavier/migrations.
    """


def downgrade() -> None:
    """Kept as a no-op, see upgrade."""
