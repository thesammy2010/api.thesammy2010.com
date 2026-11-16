"""Schemas for the places the group plays."""

import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VenueRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(
        description="What it's called, such as the club's name",
        min_length=1,
        max_length=255,
    )
    address: Optional[str] = Field(max_length=512, default=None)
    notes: Optional[str] = Field(
        description="Anything worth knowing, such as how to book a court",
        max_length=512,
        default=None,
    )
    is_active: bool = Field(
        description="Whether the group still plays there. One that isn't keeps "
        "its matches",
        default=True,
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class VenueResponse(VenueRequest):
    id: UUID
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None
