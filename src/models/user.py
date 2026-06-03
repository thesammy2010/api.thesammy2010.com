import enum
import uuid

from sqlalchemy import event, func
from sqlalchemy.engine.base import Connection
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.sql.sqltypes import DateTime, Enum, String

from src.models import Base


class Role(str, enum.Enum):
    none = "none"
    viewer = "viewer"
    editor = "editor"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    google_account_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    created_at: Mapped[uuid.UUID] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="role"), nullable=False, server_default=Role.none.value
    )
    updated_at: Mapped[uuid.UUID] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.google_account_id})>"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@event.listens_for(User, "before_insert")
def update(mapper: Mapper, connection: Connection, target: User):
    target.updated_at = func.now()
