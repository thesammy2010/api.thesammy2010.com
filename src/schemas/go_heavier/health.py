"""Schemas for Apple Health data: workouts recorded by a watch, and the
sleep and body measurements around them."""

import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from src.schemas.utils import PaginationParams


class _HealthWorkoutFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    activity_type: str = Field(
        description="HealthKit's activity type, e.g. traditional_strength_training",
        max_length=64,
    )
    start_time: AwareDatetime = Field(description="When the workout started")
    end_time: AwareDatetime = Field(description="When the workout ended")
    duration_seconds: float = Field(
        description="How long the workout ran, excluding pauses", ge=0
    )
    active_energy_kcal: Optional[float] = Field(
        description="Calories burned by moving, in kcal", ge=0, default=None
    )
    basal_energy_kcal: Optional[float] = Field(
        description="Calories burned at rest over the same time, in kcal",
        ge=0,
        default=None,
    )
    heart_rate_avg: Optional[float] = Field(
        description="Average heart rate, in bpm", gt=0, default=None
    )
    heart_rate_min: Optional[float] = Field(
        description="Lowest heart rate, in bpm", gt=0, default=None
    )
    heart_rate_max: Optional[float] = Field(
        description="Highest heart rate, in bpm", gt=0, default=None
    )
    average_mets: Optional[float] = Field(
        description="Average intensity, in METs (kcal/hr·kg)", ge=0, default=None
    )
    effort_score: Optional[int] = Field(
        description="The effort rating given on the watch, 1 to 10",
        ge=1,
        le=10,
        default=None,
    )
    estimated_effort_score: Optional[float] = Field(
        description="Apple's own estimate of the effort, 1 to 10",
        ge=0,
        le=10,
        default=None,
    )
    indoor: Optional[bool] = Field(
        description="Whether the workout was recorded as indoors", default=None
    )
    weather_temperature_c: Optional[float] = Field(
        description="Outside temperature at the time, in °C", default=None
    )
    weather_humidity_pct: Optional[float] = Field(
        description="Outside humidity at the time, 0 to 100", ge=0, le=100, default=None
    )
    time_zone: Optional[str] = Field(
        description="IANA time zone the workout was recorded in",
        max_length=64,
        default=None,
    )
    source_name: Optional[str] = Field(
        description="What recorded the workout, e.g. the watch's name",
        max_length=255,
        default=None,
    )
    device_model: Optional[str] = Field(
        description="The recording device's model identifier, e.g. Watch8,3",
        max_length=64,
        default=None,
    )

    @model_validator(mode="after")
    def ends_after_it_starts(self):
        if self.end_time < self.start_time:
            raise ValueError("end_time is before start_time")
        return self


class PutHealthWorkoutRequest(_HealthWorkoutFields):
    """A workout as read from Apple Health. Sending it again replaces it,
    keeping whichever session it's linked to."""

    heart_rate: Optional[List[Tuple[float, float]]] = Field(
        description="Every heart rate reading during the workout, as [seconds "
        "since start_time, bpm] pairs",
        default=None,
        max_length=20_000,
    )


class LinkHealthWorkoutRequest(BaseModel):
    """Links a workout to a session by hand, or unlinks it with null.
    Automatic matching leaves it alone from then on."""

    session_id: Optional[UUID] = Field(
        description="The session the workout was recorded during, or null for none"
    )


class HealthWorkoutSummary(_HealthWorkoutFields):
    """A workout without its heart rate readings, as listed."""

    id: UUID = Field(description="The HealthKit workout's UUID")
    session_id: Optional[UUID] = Field(
        description="The session the workout was recorded during, if matched",
        default=None,
    )
    session_linked_manually: bool = Field(
        description="Whether session_id was set by hand rather than matched"
    )
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None


class HealthWorkoutResponse(HealthWorkoutSummary):
    heart_rate: Optional[List[Tuple[float, float]]] = Field(
        description="Every heart rate reading during the workout, as [seconds "
        "since start_time, bpm] pairs",
        default=None,
    )


class ListHealthWorkoutsRequest(PaginationParams):
    """Query parameters for listing workouts, oldest first."""

    session_id: Optional[UUID] = Field(
        description="Only the workout linked to this session", default=None
    )
    after: Optional[AwareDatetime] = Field(
        description="Only workouts starting at or after this datetime", default=None
    )
    before: Optional[AwareDatetime] = Field(
        description="Only workouts starting at or before this datetime", default=None
    )


class _HealthDayFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sleep_start: Optional[AwareDatetime] = Field(
        description="When the night's sleep started", default=None
    )
    sleep_end: Optional[AwareDatetime] = Field(
        description="When the night's sleep ended, on this date", default=None
    )
    sleep_core_minutes: Optional[float] = Field(ge=0, default=None)
    sleep_deep_minutes: Optional[float] = Field(ge=0, default=None)
    sleep_rem_minutes: Optional[float] = Field(ge=0, default=None)
    sleep_awake_minutes: Optional[float] = Field(
        description="Minutes awake between falling asleep and waking up",
        ge=0,
        default=None,
    )
    resting_heart_rate: Optional[float] = Field(
        description="Resting heart rate, in bpm", gt=0, default=None
    )
    hrv_sdnn_ms: Optional[float] = Field(
        description="Average heart rate variability (SDNN), in ms", ge=0, default=None
    )
    respiratory_rate: Optional[float] = Field(
        description="Average breaths per minute while asleep", gt=0, default=None
    )
    vo2_max: Optional[float] = Field(
        description="Cardio fitness, in mL/min·kg", gt=0, default=None
    )
    sleeping_wrist_temperature_c: Optional[float] = Field(
        description="Wrist temperature overnight, in °C", default=None
    )
    body_mass_kg: Optional[float] = Field(
        description="The day's last weigh-in, in kg", gt=0, default=None
    )
    body_fat_pct: Optional[float] = Field(
        description="Body fat, 0 to 100", ge=0, le=100, default=None
    )
    lean_body_mass_kg: Optional[float] = Field(gt=0, default=None)
    steps: Optional[int] = Field(description="Steps over the day", ge=0, default=None)


class PutHealthDayRequest(_HealthDayFields):
    """One day as read from Apple Health. Sending it again replaces it."""


class HealthDayResponse(_HealthDayFields):
    date: datetime.date = Field(
        description="The local date. For sleep, the date it was woken up on"
    )
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None


class ListHealthDaysRequest(PaginationParams):
    """Query parameters for listing days, oldest first."""

    after: Optional[datetime.date] = Field(
        description="Only days on or after this date", default=None
    )
    before: Optional[datetime.date] = Field(
        description="Only days on or before this date", default=None
    )
