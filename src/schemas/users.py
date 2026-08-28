from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.common import UserRole
from src.schemas.utils import PaginationParams


class UpdateUserRoleRequest(BaseModel):
    role: UserRole


class CreateUserRequest(BaseModel):
    google_account_id: str
    role: UserRole = UserRole.GUEST
    # Optional labels so a pre-provisioned account isn't blank in the admin
    # list until the person actually signs in - overwritten with whatever
    # the real Google account says the first time they do.
    email: Optional[str] = None
    name: Optional[str] = None


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
