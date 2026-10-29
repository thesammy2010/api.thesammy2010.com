import datetime
import uuid
from typing import List, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import ForeignKey

from src.models import Base


class HealthWorkout(Base):
    """A workout recorded by Apple Health (an Apple Watch, normally),
    linked to the session it was recorded during once one matches.

    The id is the HealthKit workout's own UUID, so the app can resend a
    workout as often as it likes and it stays one row.
    """

    __tablename__ = "health_workouts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, nullable=False)
    # Unique: a session links to at most one workout. Deleting the session
    # unlinks the workout rather than blocking the delete.
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    # Set when session_id was chosen by hand, so automatic matching never
    # overrides it - including choosing no session at all.
    session_linked_manually: Mapped[bool] = mapped_column(
        Boolean(), nullable=False, default=False
    )

    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    start_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    # Excludes pauses, so can be shorter than end_time - start_time.
    duration_seconds: Mapped[float] = mapped_column(Float(), nullable=False)

    active_energy_kcal: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    basal_energy_kcal: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    heart_rate_avg: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    heart_rate_min: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    heart_rate_max: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    average_mets: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    # The 1-10 rating given on the watch, and Apple's own estimate.
    effort_score: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)
    estimated_effort_score: Mapped[Optional[float]] = mapped_column(
        Float(), nullable=True
    )

    indoor: Mapped[Optional[bool]] = mapped_column(Boolean(), nullable=True)
    weather_temperature_c: Mapped[Optional[float]] = mapped_column(
        Float(), nullable=True
    )
    weather_humidity_pct: Mapped[Optional[float]] = mapped_column(
        Float(), nullable=True
    )
    time_zone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    device_model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Every heart rate reading during the workout as [seconds since
    # start_time, bpm] pairs - about one every five seconds. Always read
    # whole, so a column rather than a row per reading; Postgres can still
    # unpack it with jsonb_array_elements.
    heart_rate: Mapped[Optional[List[List[float]]]] = mapped_column(
        JSONB(), nullable=True
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
        return f"<HealthWorkout(id={self.id}, start={self.start_time}, session={self.session_id})>"


class HealthDay(Base):
    """What Apple Health knows about one day: the night's sleep that ended
    on it, and that day's body measurements. A session reads the day it took
    place on, so the night before and the morning's weigh-in come with it.
    """

    __tablename__ = "health_days"

    # The local calendar date. For sleep, the date it was woken up on.
    date: Mapped[datetime.date] = mapped_column(Date(), primary_key=True)

    sleep_start: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sleep_end: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sleep_core_minutes: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    sleep_deep_minutes: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    sleep_rem_minutes: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    sleep_awake_minutes: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)

    resting_heart_rate: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    hrv_sdnn_ms: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    respiratory_rate: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    vo2_max: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    sleeping_wrist_temperature_c: Mapped[Optional[float]] = mapped_column(
        Float(), nullable=True
    )
    body_mass_kg: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    body_fat_pct: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    lean_body_mass_kg: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    steps: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)

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
        return f"<HealthDay(date={self.date})>"
