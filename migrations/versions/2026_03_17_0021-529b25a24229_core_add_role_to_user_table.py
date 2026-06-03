"""core: add role to user table

Revision ID: 529b25a24229
Revises: 77fec11e24db
Create Date: 2026-03-17 00:21:53.043048

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from src.models.user import User

# revision identifiers, used by Alembic.
revision: str = "529b25a24229"
down_revision: Union[str, Sequence[str], None] = "77fec11e24db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE role AS ENUM ('none', 'viewer', 'editor', 'admin')")
    op.add_column(
        User.__tablename__,
        sa.Column(
            "role",
            sa.Enum("none", "viewer", "editor", "admin", name="role"),
            nullable=False,
            server_default="none",
        ),
    )


def downgrade() -> None:
    op.drop_column(User.__tablename__, "role")
    op.execute("DROP TYPE role")
