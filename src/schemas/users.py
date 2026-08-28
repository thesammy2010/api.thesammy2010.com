from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from src.common import UserRole
from src.schemas.utils import PaginationParams


class UpdateUserRoleRequest(BaseModel):
    role: UserRole


class CreateUserRequest(BaseModel):
    """Either identifier works: google_account_id if an admin somehow
    already has it, or just email - the far more common case, since an
    admin knows who they want to invite by email, not by their opaque
    Google account id. An email-only row is claimed automatically (its
    google_account_id filled in) the first time that person signs in."""

    google_account_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    role: UserRole = UserRole.GUEST

    @model_validator(mode="after")
    def _require_an_identifier(self) -> "CreateUserRequest":
        if not self.google_account_id and not self.email:
            raise ValueError("Provide a google_account_id, an email, or both")
        return self


class ListUsersRequest(PaginationParams):
    """Input schema for listing users. Paginated the same way as every
    other list endpoint. Only active users are listed - deleted_at isn't
    exposed at the API level, so a deleted user would be indistinguishable
    from an active one if included."""


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRole


class AdminUserResponse(UserResponse):
    """UserResponse plus the identifying/activity fields only an admin
    needs to see - a bare id/role pair is unusable for picking someone
    out of a list."""

    email: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime
    last_signed_in_at: Optional[datetime] = None
