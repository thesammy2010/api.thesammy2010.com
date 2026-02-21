"""go_heavier: add more locations

Revision ID: 2cfd9b746fcc
Revises: 7a6ec72aacef
Create Date: 2026-02-20 23:23:04.297100

"""

from typing import Sequence, Union

import gspread
from alembic import op

from src import db
from src.config import Config
from src.models.go_heavier import Location

# revision identifiers, used by Alembic.
revision: str = "2cfd9b746fcc"
down_revision: Union[str, Sequence[str], None] = "7a6ec72aacef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


cfg = Config()
ids = [
    "97cffa7f-6b99-47a0-9a3f-adbbb7409dea",
    "5613cedb-4486-48ab-a04e-aff6e0677299",
    "37635006-a9e6-4375-b5c4-f50166ee72b6",
    "dc494b2f-cfb8-4ce4-bea5-52afcadd29d7",
    "17315633-669e-47ec-b2a0-eca769e80d7e",
    "a3b58aca-328f-4ae9-a746-6b5289a316c2",
]


def upgrade() -> None:
    if cfg.google_service_account_filepath is None:
        raise RuntimeError("Missing google service account file")
    client = gspread.service_account(filename=cfg.google_service_account_filepath)
    spreadsheet = client.open_by_key(cfg.GOOGLE_SPREADSHEET_ID)
    worksheet = spreadsheet.get_worksheet_by_id(0)
    for record in worksheet.get_all_records():
        if record["id"] in ids:
            location = Location(**record)
            print("adding {}".format(location))
            db.session.add(location)


def downgrade() -> None:
    op.execute(
        "DELETE FROM {} WHERE id IN ({})".format(
            Location.__tablename__, ",".join(f"'{id_}'" for id_ in ids)
        )
    )
