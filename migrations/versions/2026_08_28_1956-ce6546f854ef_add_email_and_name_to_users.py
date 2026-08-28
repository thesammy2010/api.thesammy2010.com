"""add email and name to users

Revision ID: ce6546f854ef
Revises: 013e3cecb33e
Create Date: 2026-08-28 19:56:50.558705

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ce6546f854ef"
down_revision: Union[str, Sequence[str], None] = "013e3cecb33e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "name")
    op.drop_column("users", "email")
