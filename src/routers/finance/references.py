"""The categories, merchants and payment methods a spend refers to."""

import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException

from src.models.finance import Category as DBCategory
from src.models.finance import Merchant as DBMerchant
from src.models.finance import PaymentMethod as DBPaymentMethod
from src.resolvers.finance import categories, merchants, payment_methods
from src.resolvers.finance.references import DuplicateName
from src.resolvers.users import require_admin
from src.routers.finance import parse_uuid
from src.schemas.finance.categories import CategoryResponse
from src.schemas.finance.merchants import MerchantRequest, MerchantResponse
from src.schemas.finance.payment_methods import (
    PaymentMethodRequest,
    PaymentMethodResponse,
)

router = APIRouter(
    prefix="/finance",
    tags=["finance reference data"],
    dependencies=[Depends(require_admin)],
)


@router.get("/categories", response_model=List[CategoryResponse])
def get_categories() -> List[DBCategory]:
    """Every category, by main category then name. They're fixed by the
    code and created by the sheet import."""
    return categories.get_categories()


@router.get("/merchants", response_model=List[MerchantResponse])
def get_merchants() -> List[DBMerchant]:
    """Every merchant, by name."""
    return merchants.get_merchants()


@router.post("/merchants", response_model=MerchantResponse)
def create_merchant(merchant: MerchantRequest) -> DBMerchant:
    """Adds a merchant. 409 if one differing only in case or spacing exists."""
    try:
        return merchants.create_merchant(merchant)
    except DuplicateName as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
def get_payment_methods() -> List[DBPaymentMethod]:
    """Every payment method, by name, including ones no longer in use."""
    return payment_methods.get_payment_methods()


@router.post("/payment-methods", response_model=PaymentMethodResponse)
def create_payment_method(payment_method: PaymentMethodRequest) -> DBPaymentMethod:
    """Adds a payment method. 409 if the name is taken."""
    try:
        return payment_methods.create_payment_method(payment_method)
    except DuplicateName as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put(
    "/payment-methods/{payment_method_id}", response_model=PaymentMethodResponse
)
def update_payment_method(
    payment_method_id: Annotated[str, uuid.UUID],
    payment_method: PaymentMethodRequest,
) -> DBPaymentMethod:
    """Replaces a payment method's fields, such as to mark it no longer in use.
    409 if the new name is taken."""
    try:
        updated = payment_methods.update_payment_method(
            payment_method_id=parse_uuid(payment_method_id, "payment method"),
            payment_method=payment_method,
        )
    except DuplicateName as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return updated
