"""allow email-only user provisioning

Revision ID: 799aecc25605
Revises: ce6546f854ef
Create Date: 2026-08-28 20:15:50.812127

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "799aecc25605"
down_revision: Union[str, Sequence[str], None] = "ce6546f854ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "users", "google_account_id", existing_type=sa.String(length=100), nullable=True
    )
    op.create_index(
        "uq_users_email_active",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_users_email_active", table_name="users")
    op.alter_column(
        "users",
        "google_account_id",
        existing_type=sa.String(length=100),
        nullable=False,
    )
