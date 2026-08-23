import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.common import IsoCountryCode
from src.schemas.utils import validate_optional_url


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
    )
    logo_url: Optional[str] = Field(
        description="URL of the location's logo",
        max_length=512,
        default=None,
    )

    @field_validator("logo_url", mode="before")
    @classmethod
    def logo_url_is_valid(cls, value: Optional[str]) -> Optional[str]:
        return validate_optional_url(value)

    address_line1: Optional[str] = Field(
        description="First line of the address",
        max_length=255,
        default=None,
    )
    address_line2: Optional[str] = Field(
        description="Second line of the address",
        max_length=255,
        default=None,
    )
    address_city: Optional[str] = Field(
        description="City of the location",
        max_length=255,
        default=None,
    )
    address_postal_code: Optional[str] = Field(
        description="Postal code of the location",
        max_length=8,
        default=None,
        pattern=r"^([A-Za-z][A-Ha-hJ-Yj-y]?[0-9][A-Za-z0-9]? ?[0-9][A-Za-z]{2}|[Gg][Ii][Rr] ?0[Aa]{2})$",
    )
    address_country_iso3: IsoCountryCode = Field(
        description="ISO 3166-1 alpha-3 country code",
        max_length=3,
        min_length=3,
        examples=list(IsoCountryCode),
        pattern=r"^[A-Z]{3}$",
    )


class LocationRequest(_BaseLocation):
    pass


class LocationResponse(_BaseLocation):
    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
