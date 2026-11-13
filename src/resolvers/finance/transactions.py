import datetime
import decimal
import uuid
from typing import Any, Dict, List, Optional

from src.config import Config
from src.db import session
from src.models.finance import Category as DBCategory
from src.models.finance import Merchant as DBMerchant
from src.models.finance import PaymentMethod as DBPaymentMethod
from src.models.finance import Transaction as DBTransaction
from src.resolvers.finance.references import (
    InvalidRelation,
    ReferenceNotFound,
    require_reference,
)
from src.schemas.finance.transactions import (
    ListTransactionsRequest,
    TransactionDetailResponse,
    TransactionRequest,
    TransactionResponse,
)


def _check_relation(
    transaction: TransactionRequest, transaction_id: Optional[uuid.UUID] = None
) -> None:
    """A spend can only belong to another that exists and belongs to none.

    Keeping it one level deep means a purchase's true cost is always just it
    plus its related spends, with no chains to follow.
    """
    if transaction.related_to_id is None:
        return
    if transaction.related_to_id == transaction_id:
        raise InvalidRelation("A transaction can't be related to itself")

    related_to = session.get(DBTransaction, transaction.related_to_id)
    if related_to is None:
        raise ReferenceNotFound(f"Transaction {transaction.related_to_id} not found")
    if related_to.related_to_id is not None:
        raise InvalidRelation(
            f"Transaction {related_to.id} already belongs to {related_to.related_to_id}, "
            "relate this one to that instead"
        )
    if transaction_id is not None and _related(transaction_id):
        raise InvalidRelation(
            "This transaction has others related to it, so can't itself be "
            "related to another"
        )


def _fields(
    transaction: TransactionRequest, transaction_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """The request's fields as the model stores them, checking what they refer to."""
    require_reference(DBPaymentMethod, transaction.payment_method_id, "Payment method")
    require_reference(DBMerchant, transaction.merchant_id, "Merchant")
    require_reference(DBCategory, transaction.category_id, "Category")
    _check_relation(transaction, transaction_id)

    fields = transaction.model_dump()
    if transaction.time_of_day is not None:
        fields["time_of_day"] = transaction.time_of_day.value
    if transaction.relation is not None:
        fields["relation"] = transaction.relation.value
    return fields


def _related(transaction_id: uuid.UUID) -> List[DBTransaction]:
    return (
        session.query(DBTransaction)
        .filter(DBTransaction.related_to_id == transaction_id)
        .order_by(DBTransaction.spent_on, DBTransaction.created_at)
        .all()
    )


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
    if request.related_to_id:
        conditions.append(DBTransaction.related_to_id == request.related_to_id)

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


def _rate(
    original_amount: Optional[decimal.Decimal], amount_gbp: decimal.Decimal
) -> Optional[float]:
    if original_amount is None or not amount_gbp:
        return None
    return round(float(original_amount / amount_gbp), 6)


def get_transaction_detail(
    transaction_id: uuid.UUID,
) -> Optional[TransactionDetailResponse]:
    """One spend, with the spends that belong to it and what it came to."""
    transaction = get_transaction(transaction_id)
    if not transaction:
        return None

    related = _related(transaction_id)
    total = transaction.amount_gbp + sum(
        (row.amount_gbp for row in related), decimal.Decimal(0)
    )
    return TransactionDetailResponse(
        **TransactionResponse.model_validate(transaction).model_dump(),
        related=[TransactionResponse.model_validate(row) for row in related],
        total_gbp=total,
        exchange_rate=_rate(transaction.original_amount, transaction.amount_gbp),
        effective_exchange_rate=_rate(transaction.original_amount, total),
    )


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

    for field, value in _fields(transaction, transaction_id).items():
        setattr(db_transaction, field, value)
    db_transaction.updated_at = datetime.datetime.now(tz=datetime.timezone.utc)

    session.commit()
    return db_transaction


def delete_transaction(transaction_id: uuid.UUID) -> bool:
    """Deletes a spend, keeping the ones related to it but unlinking them."""
    transaction = get_transaction(transaction_id)
    if not transaction:
        return False
    for row in _related(transaction_id):
        row.related_to_id = None
        row.relation = None
    session.flush()
    session.delete(transaction)
    session.commit()
    return True
