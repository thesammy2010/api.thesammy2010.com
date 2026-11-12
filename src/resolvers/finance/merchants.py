import datetime
from typing import List

from sqlalchemy import func

from src.db import session
from src.migration_utils.finance_rows import merchant_id_for, merchant_key
from src.models.finance import Merchant as DBMerchant
from src.resolvers.finance.references import DuplicateName
from src.schemas.finance.merchants import MerchantRequest


def get_merchants() -> List[DBMerchant]:
    return session.query(DBMerchant).order_by(func.lower(DBMerchant.name)).all()


def create_merchant(merchant: MerchantRequest) -> DBMerchant:
    """Adds a merchant, with the id the sheet import would give it.

    That way a spend imported later with the same merchant joins this one
    rather than failing on the name being taken.
    """
    name = " ".join(merchant.name.split())
    existing = (
        session.query(DBMerchant)
        .filter(func.lower(DBMerchant.name) == merchant_key(name))
        .first()
    )
    if existing:
        raise DuplicateName(f"Merchant {existing.name} already exists")

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    new_merchant = DBMerchant(
        id=merchant_id_for(name), name=name, created_at=now, updated_at=now
    )
    session.add(new_merchant)
    session.commit()
    return new_merchant
