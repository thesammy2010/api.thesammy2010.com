"""Schemas for the aggregated view across workouts."""

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


class WorkoutStatsRequest(BaseModel):
    """Query parameters for narrowing the workout stats."""

    model_config = ConfigDict(from_attributes=True)

    location_id: Optional[UUID] = Field(
        description="Only count workouts performed at this location",
        default=None,
    )
    exercise_id: Optional[UUID] = Field(
        description="Only count workouts of this exercise",
        default=None,
    )
    after: Optional[AwareDatetime] = Field(
        description="Only count workouts performed at or after this datetime",
        default=None,
    )
    before: Optional[AwareDatetime] = Field(
        description="Only count workouts performed at or before this datetime",
        default=None,
    )
    top_locations: int = Field(
        description="How many locations to include in the breakdown, most sets first",
        default=5,
        ge=1,
        le=25,
    )
    top_exercises: int = Field(
        description="How many exercises to include in the breakdown, most sets first",
        default=5,
        ge=1,
        le=25,
    )


class LocationBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location_id: UUID = Field(description="Unique identifier for the location")
    name: str = Field(description="Name of the location")
    sessions: int = Field(description="Number of sessions at this location")
    sets: int = Field(description="Number of sets logged at this location")
    repetitions: int = Field(description="Total repetitions across those sets")
    volume_kg: float = Field(
        description="Total weight moved, the sum of weight_kg multiplied by repetitions"
    )


class ExerciseBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exercise_id: UUID = Field(description="Unique identifier for the exercise")
    name: str = Field(description="Name of the exercise")
    sessions: int = Field(description="Number of sessions that included this exercise")
    sets: int = Field(description="Number of sets logged for this exercise")
    repetitions: int = Field(description="Total repetitions across those sets")
    volume_kg: float = Field(
        description="Total weight moved, the sum of weight_kg multiplied by repetitions"
    )


class WorkoutStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sessions: int = Field(description="Number of distinct workout sessions")
    first_workout: Optional[AwareDatetime] = Field(
        description="Time of the earliest workout counted", default=None
    )
    last_workout: Optional[AwareDatetime] = Field(
        description="Time of the most recent workout counted", default=None
    )
    total_sets: int = Field(description="Number of sets logged")
    total_repetitions: int = Field(description="Total repetitions across every set")
    total_volume_kg: float = Field(
        description="Total weight moved, the sum of weight_kg multiplied by repetitions"
    )
    heaviest_weight_kg: Optional[float] = Field(
        description="The heaviest single weight lifted", default=None
    )
    average_sets_per_session: float = Field(
        description="Mean number of sets per session, 0 when there are no sessions"
    )
    average_exercises_per_session: float = Field(
        description="Mean number of different exercises in a single session, "
        "0 when there are no sessions"
    )
    average_repetitions_per_set: float = Field(
        description="Mean number of repetitions per set, 0 when there are no sets"
    )
    distinct_locations: int = Field(
        description="Number of different locations trained at"
    )
    distinct_exercises: int = Field(description="Number of different exercises trained")
    top_locations: List[LocationBreakdown] = Field(
        description="Per location breakdown, most sets first",
        default_factory=list,
    )
    top_exercises: List[ExerciseBreakdown] = Field(
        description="Per exercise breakdown, most sets first",
        default_factory=list,
    )

    @field_validator("first_workout", "last_workout", mode="before")
    @classmethod
    def ensure_timezone_aware(cls, value):
        """Convert naive datetimes to timezone-aware datetimes (UTC)"""
        if value is None:
            return None
        if isinstance(value, datetime.datetime) and value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value
