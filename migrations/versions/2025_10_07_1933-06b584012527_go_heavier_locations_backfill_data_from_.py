"""go_heavier: locations: backfill data from csv

Revision ID: 06b584012527
Revises: aa543e109b6f
Create Date: 2025-10-07 19:33:18.106478

"""

import csv
import pathlib
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "06b584012527"
down_revision: Union[str, Sequence[str], None] = "aa543e109b6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

folder = pathlib.Path(__file__).parent
file_name = (
    folder / ".." / "data" / "go-heavier" / "locations" / "2025-10-07T18:11:05Z.csv"
)


def upgrade() -> None:
    table = sa.table(
        "locations",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("address_line1", sa.String),
        sa.column("address_line2", sa.String),
        sa.column("address_city", sa.String),
        sa.column("address_postal_code", sa.String),
        sa.column("address_country_iso3", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    with open(file_name) as csvfile:
        reader = csv.DictReader(csvfile)
        op.bulk_insert(table=table, rows=list(reader))


def downgrade() -> None:
    with open(file_name) as csvfile:
        reader = csv.DictReader(csvfile)
        op.execute(
            "DELETE FROM locations WHERE id IN ("
            + ",".join([f"'{row['id']}'" for row in reader])
            + ");"
        )
