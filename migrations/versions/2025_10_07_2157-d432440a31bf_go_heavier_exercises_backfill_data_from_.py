"""go_heavier: exercises: backfill data from csv

Revision ID: d432440a31bf
Revises: 6f2dae00bb77
Create Date: 2025-10-07 21:57:53.719342

"""

import csv
import pathlib
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from src.common import strtobool

# revision identifiers, used by Alembic.
revision: str = "d432440a31bf"
down_revision: Union[str, Sequence[str], None] = "6f2dae00bb77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


folder = pathlib.Path(__file__).parent
file_name = (
    folder / ".." / "data" / "go-heavier" / "exercises" / "2025-10-07T20:56:09Z.csv"
)


def upgrade() -> None:
    table = sa.table(
        "exercises",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("muscle_group", sa.String),
        sa.column("specific_muscle", sa.String),
        sa.column("bipedal", sa.Boolean),
        sa.column("image_url", sa.String),
        sa.column("free_weights", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    with open(file_name) as csvfile:
        reader = csv.DictReader(csvfile)
        rows = [
            {
                **row,
                "bipedal": strtobool(row["bipedal"]),
                "free_weights": strtobool(row["free_weights"]),
            }
            for row in list(reader)
        ]
        op.bulk_insert(table=table, rows=rows)


def downgrade() -> None:
    with open(file_name) as csvfile:
        reader = csv.DictReader(csvfile)
        op.execute(
            "DELETE FROM exercises WHERE id IN ("
            + ",".join([f"'{row['id']}'" for row in reader])
            + ");"
        )
