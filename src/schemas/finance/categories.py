import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group: str = Field(description="The main category, such as Food & Drink")
    name: str = Field(description="The category, such as Dinner")
    created_at: datetime.datetime
    updated_at: datetime.datetime
