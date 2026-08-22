import datetime
import uuid

import pendulum
from sqlalchemy import DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import ForeignKey

from src.models import Base


class Session(Base):
    """A single visit to a gym, holding every set performed while there."""

    __tablename__ = "sessions"
    __table_args__ = (UniqueConstraint("location_id", "workout_time"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id"), nullable=False
    )
    workout_time: Mapped[pendulum.DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.datetime.now
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(),
        nullable=True,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, time={self.workout_time})>"
