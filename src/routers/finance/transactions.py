import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from src.models.finance import Transaction as DBTransaction
from src.resolvers.finance import transactions
from src.resolvers.finance.references import ReferenceNotFound
from src.resolvers.users import require_admin
from src.routers.finance import parse_uuid
from src.schemas.finance.transactions import (
    ListTransactionsRequest,
    TransactionRequest,
    TransactionResponse,
)

# Every finance route is admin-only, set once here so that a new route can't
# be added without it
router = APIRouter(
    prefix="/finance",
    tags=["transactions"],
    dependencies=[Depends(require_admin)],
)


@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(
    request: Annotated[ListTransactionsRequest, Query()],
) -> List[DBTransaction]:
    """Lists spends, most recent first."""
    return transactions.get_transactions(request=request)


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: Annotated[str, uuid.UUID]) -> DBTransaction:
    """A single spend by id."""
    transaction = transactions.get_transaction(
        parse_uuid(transaction_id, "transaction")
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.post("/transactions", response_model=TransactionResponse)
def create_transaction(transaction: TransactionRequest) -> DBTransaction:
    """Records a spend. 404 if its payment method, merchant or category
    doesn't exist."""
    try:
        return transactions.create_transaction(transaction)
    except ReferenceNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: Annotated[str, uuid.UUID], transaction: TransactionRequest
) -> DBTransaction:
    """Replaces every field of a spend, so one left out or sent as null is
    cleared."""
    try:
        updated = transactions.update_transaction(
            transaction_id=parse_uuid(transaction_id, "transaction"),
            transaction=transaction,
        )
    except ReferenceNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return updated


@router.delete("/transactions/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: Annotated[str, uuid.UUID]) -> Response:
    """Deletes a spend. One imported from the sheet comes back on the next
    import unless it's removed from the sheet too."""
    if not transactions.delete_transaction(parse_uuid(transaction_id, "transaction")):
        raise HTTPException(status_code=404, detail="Transaction not found")
    return Response(status_code=204)
