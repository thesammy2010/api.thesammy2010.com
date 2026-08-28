"""add last_signed_in_at to users

Revision ID: 013e3cecb33e
Revises: c5093f491826
Create Date: 2026-08-28 19:49:06.767155

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "013e3cecb33e"
down_revision: Union[str, Sequence[str], None] = "c5093f491826"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("last_signed_in_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "last_signed_in_at")
