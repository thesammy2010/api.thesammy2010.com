import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.finance.enums import PaymentMethodKind


class PaymentMethodRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(
        description="The card or account, such as Barclaycard",
        min_length=1,
        max_length=64,
    )
    kind: PaymentMethodKind = Field(description="What sort of payment method it is")
    is_active: bool = Field(
        description="Whether it's still in use. One that isn't can still be "
        "set on a spend, so older ones keep theirs",
        default=True,
    )


class PaymentMethodResponse(PaymentMethodRequest):
    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
