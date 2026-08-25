from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.common import UserRole


class UpdateUserRoleRequest(BaseModel):
    role: UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRole
