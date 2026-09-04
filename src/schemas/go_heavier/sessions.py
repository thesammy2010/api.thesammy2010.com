"""Schemas for a workout session, the sets sharing one workout_time."""

import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from src.schemas.utils import PaginationParams


class ListSessionsRequest(PaginationParams):
    """Query parameters for listing sessions, most recent first."""

    model_config = ConfigDict(from_attributes=True)

    location_id: Optional[UUID] = Field(
        description="Only list sessions at this location",
        default=None,
    )
    exercise_id: Optional[UUID] = Field(
        description="Only list sessions that included this exercise. The totals "
        "still cover the whole session, not just that exercise",
        default=None,
    )
    after: Optional[AwareDatetime] = Field(
        description="Only list sessions at or after this datetime",
        default=None,
    )
    before: Optional[AwareDatetime] = Field(
        description="Only list sessions at or before this datetime",
        default=None,
    )


class _BaseSession(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique identifier for the session")
    workout_time: AwareDatetime = Field(description="When the session took place")
    location_id: UUID = Field(description="Unique identifier for the location")
    location: str = Field(description="Name of the location")
    sets: int = Field(description="Number of sets logged in the session")
    exercises: int = Field(description="Number of different exercises in the session")
    repetitions: int = Field(description="Total repetitions across the session")
    volume_kg: float = Field(
        description="Total weight moved, the sum of weight_kg multiplied by repetitions"
    )
    heaviest_weight_kg: Optional[float] = Field(
        description="The heaviest single weight lifted in the session, null "
        "while nothing has been logged against it yet",
        default=None,
    )
    duration_minutes: Optional[int] = Field(
        description="How long the session lasted, in minutes", default=None
    )
    calories_burned_kcal: Optional[int] = Field(
        description="Calories burned during the session, in kcal", default=None
    )
    took_preworkout: Optional[bool] = Field(
        description="Whether pre-workout was taken that day", default=None
    )
    went_to_office: Optional[bool] = Field(
        description="Whether the caller went into the office that day", default=None
    )
    sleep_hours: Optional[float] = Field(
        description="Hours slept the night before", default=None
    )
    bed_time: Optional[AwareDatetime] = Field(
        description="What time the caller went to bed the night before",
        default=None,
    )
    sleep_score: Optional[int] = Field(
        description="Sleep score from Apple Health for the night before",
        default=None,
    )

    @field_validator("workout_time", "bed_time", mode="before")
    @classmethod
    def ensure_timezone_aware(cls, value):
        """Convert naive datetimes to timezone-aware datetimes (UTC)"""
        if value is None:
            return None
        if isinstance(value, datetime.datetime) and value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value


class SessionExerciseStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exercise_id: UUID = Field(description="Unique identifier for the exercise")
    name: str = Field(description="Name of the exercise")
    sets: int = Field(description="Number of sets of this exercise in the session")
    repetitions: int = Field(description="Total repetitions across those sets")
    volume_kg: float = Field(
        description="Total weight moved, the sum of weight_kg multiplied by repetitions"
    )
    heaviest_weight_kg: float = Field(
        description="The heaviest single weight lifted for this exercise"
    )


class CreateSessionRequest(BaseModel):
    """A visit to a gym, to log sets against."""

    model_config = ConfigDict(from_attributes=True)

    location_id: UUID = Field(description="Where the session took place")
    workout_time: AwareDatetime = Field(description="When the session took place")


class UpdateSessionRequest(BaseModel):
    """Enrichment for a session, set separately from its sets - typically
    afterwards, once a duration/calorie figure or the previous night's sleep
    data is available. Every field is optional and only the ones given are
    changed; the rest are left as they were."""

    model_config = ConfigDict(from_attributes=True)

    duration_minutes: Optional[int] = Field(
        description="How long the session lasted, in minutes", default=None
    )
    calories_burned_kcal: Optional[int] = Field(
        description="Calories burned during the session, in kcal", default=None
    )
    took_preworkout: Optional[bool] = Field(
        description="Whether pre-workout was taken that day", default=None
    )
    went_to_office: Optional[bool] = Field(
        description="Whether the caller went into the office that day", default=None
    )
    sleep_hours: Optional[float] = Field(
        description="Hours slept the night before", default=None
    )
    bed_time: Optional[AwareDatetime] = Field(
        description="What time the caller went to bed the night before",
        default=None,
    )
    sleep_score: Optional[int] = Field(
        description="Sleep score from Apple Health for the night before",
        default=None,
    )

    @field_validator("bed_time", mode="before")
    @classmethod
    def ensure_timezone_aware(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime.datetime) and value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value


class SessionSummary(_BaseSession):
    pass


class SessionResponse(_BaseSession):
    by_exercise: List[SessionExerciseStats] = Field(
        description="Per exercise breakdown, in the order the exercises were performed",
        default_factory=list,
    )
