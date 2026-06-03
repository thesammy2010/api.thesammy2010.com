import uuid

from pydantic import BaseModel

from src.models.user import Role


class UserResponse(BaseModel):
    id: uuid.UUID
    google_account_id: str
    role: Role

    model_config = {"from_attributes": True}


class UpdateUserRequest(BaseModel):
    id: uuid.UUID
    role: Role
