import datetime
import uuid
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class Venue(Base):
    """Somewhere the group plays."""

    __tablename__ = "squash_venues"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    address: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    # No longer played at, without losing the matches played there
    is_active: Mapped[bool] = mapped_column(
        Boolean(), nullable=False, server_default="true"
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.datetime.now
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(),
        nullable=True,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    )

    def __repr__(self) -> str:
        return f"<Venue(id={self.id}, name={self.name})>"
