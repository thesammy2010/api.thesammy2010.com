"""add role to users

Revision ID: be30e3d18976
Revises: 5679283b9822
Create Date: 2026-08-24 23:19:03.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "be30e3d18976"
down_revision: Union[str, Sequence[str], None] = "5679283b9822"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=50), server_default="guest", nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "role")
