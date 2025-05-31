import uuid

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    google_account_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )

    def __repr__(self) -> str:
        return f"<Player(id={self.id}, name={self.google_account_id})>"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
