import datetime
import uuid
from typing import Any, Dict, List, Optional

from src.config import Config
from src.db import session
from src.models.finance import Category as DBCategory
from src.models.finance import Merchant as DBMerchant
from src.models.finance import PaymentMethod as DBPaymentMethod
from src.models.finance import Transaction as DBTransaction
from src.resolvers.finance.references import require_reference
from src.schemas.finance.transactions import (
    ListTransactionsRequest,
    TransactionRequest,
)


def _fields(transaction: TransactionRequest) -> Dict[str, Any]:
    """The request's fields as the model stores them, checking what they refer to."""
    require_reference(DBPaymentMethod, transaction.payment_method_id, "Payment method")
    require_reference(DBMerchant, transaction.merchant_id, "Merchant")
    require_reference(DBCategory, transaction.category_id, "Category")

    fields = transaction.model_dump()
    if transaction.time_of_day is not None:
        fields["time_of_day"] = transaction.time_of_day.value
    return fields


def get_transactions(request: ListTransactionsRequest) -> List[DBTransaction]:
    """List spends, most recent first."""
    conditions = []
    if request.after:
        conditions.append(DBTransaction.spent_on >= request.after)
    if request.before:
        conditions.append(DBTransaction.spent_on <= request.before)
    if request.category_id:
        conditions.append(DBTransaction.category_id == request.category_id)
    if request.merchant_id:
        conditions.append(DBTransaction.merchant_id == request.merchant_id)
    if request.payment_method_id:
        conditions.append(DBTransaction.payment_method_id == request.payment_method_id)

    return (
        session.query(DBTransaction)
        .filter(*conditions)
        # Then by when they were added, so a day's spends keep a stable order
        # from one page to the next
        .order_by(
            DBTransaction.spent_on.desc(),
            DBTransaction.created_at.desc(),
            DBTransaction.id,
        )
        .limit(Config.DEFAULT_DB_PAGE_SIZE)
        .offset(request.offset)
        .all()
    )


def get_transaction(transaction_id: uuid.UUID) -> Optional[DBTransaction]:
    return session.get(DBTransaction, transaction_id)


def create_transaction(transaction: TransactionRequest) -> DBTransaction:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    new_transaction = DBTransaction(
        id=uuid.uuid4(), **_fields(transaction), created_at=now, updated_at=now
    )
    session.add(new_transaction)
    session.commit()
    return new_transaction


def update_transaction(
    transaction_id: uuid.UUID, transaction: TransactionRequest
) -> Optional[DBTransaction]:
    """Replaces every field, so one sent as null is cleared."""
    db_transaction = get_transaction(transaction_id)
    if not db_transaction:
        return None

    for field, value in _fields(transaction).items():
        setattr(db_transaction, field, value)
    db_transaction.updated_at = datetime.datetime.now(tz=datetime.timezone.utc)

    session.commit()
    return db_transaction


def delete_transaction(transaction_id: uuid.UUID) -> bool:
    transaction = get_transaction(transaction_id)
    if not transaction:
        return False
    session.delete(transaction)
    session.commit()
    return True
