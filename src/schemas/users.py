from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.common import UserRole


class UpdateUserRoleRequest(BaseModel):
    role: UserRole


class CreateUserRequest(BaseModel):
    google_account_id: str
    role: UserRole = UserRole.GUEST


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRole
    deleted_at: Optional[datetime] = None
