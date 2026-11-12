import datetime
import uuid
from typing import List, Optional

from src.db import session
from src.migration_utils.finance_rows import payment_method_id_for
from src.models.finance import PaymentMethod as DBPaymentMethod
from src.resolvers.finance.references import DuplicateName
from src.schemas.finance.payment_methods import PaymentMethodRequest


def get_payment_methods() -> List[DBPaymentMethod]:
    return session.query(DBPaymentMethod).order_by(DBPaymentMethod.name).all()


def _check_name_free(name: str, payment_method_id: Optional[uuid.UUID] = None):
    existing = session.query(DBPaymentMethod).filter(DBPaymentMethod.name == name)
    if payment_method_id is not None:
        existing = existing.filter(DBPaymentMethod.id != payment_method_id)
    if existing.first():
        raise DuplicateName(f"Payment method {name} already exists")


def create_payment_method(payment_method: PaymentMethodRequest) -> DBPaymentMethod:
    """Adds a payment method, with the id the sheet import would give it."""
    _check_name_free(payment_method.name)

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    new_payment_method = DBPaymentMethod(
        id=payment_method_id_for(payment_method.name),
        name=payment_method.name,
        kind=payment_method.kind.value,
        is_active=payment_method.is_active,
        created_at=now,
        updated_at=now,
    )
    session.add(new_payment_method)
    session.commit()
    return new_payment_method


def update_payment_method(
    payment_method_id: uuid.UUID, payment_method: PaymentMethodRequest
) -> Optional[DBPaymentMethod]:
    db_payment_method = session.get(DBPaymentMethod, payment_method_id)
    if not db_payment_method:
        return None
    _check_name_free(payment_method.name, payment_method_id)

    db_payment_method.name = payment_method.name
    db_payment_method.kind = payment_method.kind.value
    db_payment_method.is_active = payment_method.is_active
    db_payment_method.updated_at = datetime.datetime.now(tz=datetime.timezone.utc)

    session.commit()
    return db_payment_method
