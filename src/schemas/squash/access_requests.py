"""Schemas for asking to join the squash group, and reviewing those asks."""

import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.schemas.squash.enums import AccessRequestStatus


class AccessRequestRequest(BaseModel):
    message: Optional[str] = Field(
        description="Anything the admin should know, such as who they play with",
        max_length=500,
        default=None,
    )

    @field_validator("message", mode="before")
    @classmethod
    def blank_is_none(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not str(value).strip():
            return None
        return str(value).strip()


class AccessRequestResponse(BaseModel):
    """A request as the person who made it sees it."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: AccessRequestStatus
    message: Optional[str] = None
    player_id: Optional[UUID] = Field(
        description="The player they became, once approved", default=None
    )
    reviewed_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime


class AdminAccessRequestResponse(AccessRequestResponse):
    """A request with who made it, for an admin reviewing it."""

    user_id: UUID
    name: Optional[str] = Field(description="Their Google account's name")
    email: Optional[str] = Field(description="Their Google account's email")
    reviewed_by_id: Optional[UUID] = None

    @classmethod
    def of(cls, request) -> "AdminAccessRequestResponse":
        return cls.model_validate(
            {
                **AccessRequestResponse.model_validate(request).model_dump(),
                "user_id": request.user_id,
                "name": request.user.name,
                "email": request.user.email,
                "reviewed_by_id": request.reviewed_by_id,
            }
        )


class ListAccessRequestsRequest(BaseModel):
    status: Optional[AccessRequestStatus] = Field(
        description="Only requests in this state, such as pending. All when left out",
        default=None,
    )


class ApproveAccessRequestRequest(BaseModel):
    player_id: Optional[UUID] = Field(
        description="An existing player to make them, such as someone already "
        "recorded in matches who has no user yet. Left out, they're added as "
        "a new player",
        default=None,
    )
    name: Optional[str] = Field(
        description="What a new player is called. Defaults to their Google "
        "account's name",
        min_length=1,
        max_length=255,
        default=None,
    )

    @field_validator("name", mode="before")
    @classmethod
    def blank_is_none(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not str(value).strip():
            return None
        return str(value).strip()
