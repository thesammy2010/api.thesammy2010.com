"""add deleted_at to users and user_audit_log table

Revision ID: c5093f491826
Revises: be30e3d18976
Create Date: 2026-08-28 18:40:00.195422

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5093f491826"
down_revision: Union[str, Sequence[str], None] = "be30e3d18976"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.drop_constraint(op.f("uq_users_google_account_id"), "users", type_="unique")
    op.create_index(
        "uq_users_google_account_id_active",
        "users",
        ["google_account_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_table(
        "user_audit_log",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("target_user_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("previous_role", sa.String(length=50), nullable=True),
        sa.Column("new_role", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["users.id"], name=op.f("fk_user_audit_log_actor_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["target_user_id"],
            ["users.id"],
            name=op.f("fk_user_audit_log_target_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_audit_log")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("user_audit_log")
    op.drop_index("uq_users_google_account_id_active", table_name="users")
    op.create_unique_constraint(
        op.f("uq_users_google_account_id"), "users", ["google_account_id"]
    )
    op.drop_column("users", "deleted_at")
