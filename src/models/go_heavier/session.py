import datetime
import uuid
from typing import Optional

import pendulum
from sqlalchemy import Boolean, DateTime, Float, Integer, UniqueConstraint, func
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

    # Enrichment set separately via PATCH, once the session's sets are
    # already logged - none of these are known while a session is being
    # actively worked, only afterwards (from a watch/tracker, or the night
    # before for the sleep fields).
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)
    calories_burned_kcal: Mapped[Optional[int]] = mapped_column(
        Integer(), nullable=True
    )
    took_preworkout: Mapped[Optional[bool]] = mapped_column(Boolean(), nullable=True)
    went_to_office: Mapped[Optional[bool]] = mapped_column(Boolean(), nullable=True)
    sleep_hours: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    bed_time: Mapped[Optional[pendulum.DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sleep_score: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)

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
