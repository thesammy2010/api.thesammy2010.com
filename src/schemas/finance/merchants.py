import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MerchantRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="Who was paid", min_length=1, max_length=255)


class MerchantResponse(MerchantRequest):
    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
