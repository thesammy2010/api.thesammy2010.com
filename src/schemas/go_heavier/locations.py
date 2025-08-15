import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.common import IsoCountryCode


class _BaseLocation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(
        description="Name of the location",
        max_length=255,
    )
    description: Optional[str] = Field(
        description="Description of the location",
        max_length=255,
        default=None,
        nullable=True,
    )
    address_line1: Optional[str] = Field(
        description="First line of the address",
        max_length=255,
        default=None,
        nullable=True,
    )
    address_line2: Optional[str] = Field(
        description="Second line of the address",
        max_length=255,
        default=None,
        nullable=True,
    )
    address_city: Optional[str] = Field(
        description="City of the location",
        max_length=255,
        default=None,
        nullable=True,
    )
    address_country_iso3: IsoCountryCode = Field(
        description="ISO 3166-1 alpha-3 country code",
        max_length=3,
        min_length=3,
        examples=list(IsoCountryCode),
        pattern=r"^[A-Z]{3}$",
        nullable=False,
    )


class LocationRequest(_BaseLocation):
    pass


class LocationResponse(_BaseLocation):
    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
