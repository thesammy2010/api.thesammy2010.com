import datetime
import uuid
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import ForeignKey

from src.models import Base


class SleepRecord(Base):
    """A parsed Sleep Analysis export, stored on arrival since it usually
    shows up before the session it belongs with even exists.

    Matched onto a session by wake_time's calendar date (see
    resolvers.go_heavier.sessions.create_session) - "last night's sleep"
    pairs with "today's gym session" even when bed_time was technically the
    day before. matched_session_id records that a match already happened,
    so a record is never attached to two sessions.
    """

    __tablename__ = "sleep_records"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    bed_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    wake_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sleep_hours: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    sleep_score: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)
    stages_minutes: Mapped[Optional[dict]] = mapped_column(JSON(), nullable=True)
    # SET NULL rather than RESTRICT: deleting a session is a normal,
    # supported action, and the record having pointed at it doesn't mean
    # the record itself should be deleted or the session delete blocked.
    # A freed record is eligible to match a future session again.
    matched_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    def __repr__(self) -> str:
        return f"<SleepRecord(id={self.id}, wake_time={self.wake_time})>"
