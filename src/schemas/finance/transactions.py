"""Schemas for a single spend."""

import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.schemas.finance.enums import TimeOfDay
from src.schemas.finance.money import Money
from src.schemas.utils import PaginationParams


class ListTransactionsRequest(PaginationParams):
    """Query parameters for listing spends, most recent first."""

    model_config = ConfigDict(from_attributes=True)

    after: Optional[datetime.date] = Field(
        description="Only list spends on or after this date", default=None
    )
    before: Optional[datetime.date] = Field(
        description="Only list spends on or before this date", default=None
    )
    category_id: Optional[UUID] = Field(
        description="Only list spends in this category", default=None
    )
    merchant_id: Optional[UUID] = Field(
        description="Only list spends with this merchant", default=None
    )
    payment_method_id: Optional[UUID] = Field(
        description="Only list spends paid with this payment method", default=None
    )

    @model_validator(mode="after")
    def validate_range(self) -> "ListTransactionsRequest":
        if self.after and self.before and self.after > self.before:
            raise ValueError("after must not be later than before")
        return self


class TransactionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    spent_on: datetime.date = Field(description="The day the money was spent")
    amount_gbp: Money = Field(
        description="How much was spent in GBP. Negative for a refund",
        max_digits=12,
        decimal_places=4,
    )
    original_amount: Optional[Money] = Field(
        description="How much was charged in the local currency, for a spend abroad",
        max_digits=14,
        decimal_places=4,
        default=None,
    )
    original_currency: Optional[str] = Field(
        description="ISO 4217 code of original_amount's currency",
        pattern=r"^[A-Z]{3}$",
        default=None,
    )
    payment_method_id: UUID = Field(description="What it was paid with")
    merchant_id: Optional[UUID] = Field(description="Who was paid", default=None)
    category_id: Optional[UUID] = Field(
        description="What it was spent on", default=None
    )
    description: Optional[str] = Field(
        description="What it was for", max_length=512, default=None
    )
    is_necessary: Optional[bool] = Field(
        description="Whether it had to be spent. Null when it wasn't recorded",
        default=None,
    )
    is_recurring: Optional[bool] = Field(
        description="Whether it's spent regularly, such as a subscription",
        default=None,
    )
    with_partner: Optional[bool] = Field(
        description="Whether it was spent together with a partner", default=None
    )
    time_of_day: Optional[TimeOfDay] = Field(
        description="When in the day it was spent, or online", default=None
    )

    @model_validator(mode="after")
    def validate_original_amount(self) -> "TransactionRequest":
        if self.original_currency and self.original_amount is None:
            raise ValueError("original_currency is set without original_amount")
        return self


class TransactionResponse(TransactionRequest):
    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
