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


class ListUsersRequest(PaginationParams):
    """Input schema for listing users. Paginated the same way as every
    other list endpoint; no filters yet since admins are expected to want
    everyone, deleted included."""


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRole
    deleted_at: Optional[datetime] = None
