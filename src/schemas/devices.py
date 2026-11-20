"""Schemas for the phones that get notifications."""

import datetime
import enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DeviceEnvironment(str, enum.Enum):
    # A build run from Xcode, whose tokens only Apple's sandbox accepts
    SANDBOX = "sandbox"
    # TestFlight and the App Store
    PRODUCTION = "production"


class DeviceRequest(BaseModel):
    token: str = Field(
        description="The APNs device token the app was given, as hex",
        pattern=r"^[0-9a-fA-F]{64,200}$",
    )
    app: str = Field(
        description="The app's bundle ID, such as com.thesammy2010.how2squash.app",
        pattern=r"^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$",
        max_length=255,
    )
    environment: DeviceEnvironment = Field(
        description="Which of Apple's push servers the token is for: sandbox "
        "for a build run from Xcode, production for TestFlight or the App Store",
    )

    @field_validator("token", mode="after")
    @classmethod
    def lowercase_token(cls, value: str) -> str:
        """Hex either way round is the same token, so it's stored one way."""
        return value.lower()


class DeviceResponse(DeviceRequest):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime.datetime
    last_registered_at: datetime.datetime
