"""Schemas for the aggregated view of an exercise's workout history."""

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


class ExerciseStatsRequest(BaseModel):
    """Query parameters for narrowing an exercise's stats."""

    model_config = ConfigDict(from_attributes=True)

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


class LocationStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location_id: UUID = Field(description="Unique identifier for the location")
    name: str = Field(description="Name of the location")
    sessions: int = Field(
        description="Number of sessions at this location that included the exercise"
    )
    sets: int = Field(description="Number of sets of the exercise at this location")
    repetitions: int = Field(description="Total repetitions across those sets")
    volume_kg: float = Field(
        description="Total weight moved, the sum of weight_kg multiplied by repetitions"
    )


class ExerciseStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exercise_id: UUID = Field(description="Unique identifier for the exercise")
    name: str = Field(description="Name of the exercise")
    sessions: int = Field(
        description="Number of distinct workout sessions that included this exercise"
    )
    first_performed: Optional[AwareDatetime] = Field(
        description="Time this exercise was first performed", default=None
    )
    last_performed: Optional[AwareDatetime] = Field(
        description="Time this exercise was most recently performed", default=None
    )
    total_sets: int = Field(description="Number of sets logged for this exercise")
    total_repetitions: int = Field(
        description="Total repetitions across every set of this exercise"
    )
    total_volume_kg: float = Field(
        description="Total weight moved, the sum of weight_kg multiplied by repetitions"
    )
    heaviest_weight_kg: Optional[float] = Field(
        description="The heaviest single weight lifted for this exercise", default=None
    )
    average_sets_per_session: float = Field(
        description="Mean number of sets per session, 0 when there are no sessions"
    )
    average_repetitions_per_set: float = Field(
        description="Mean number of repetitions per set, 0 when there are no sets"
    )
    distinct_locations: int = Field(
        description="Number of different locations this exercise was performed at"
    )
    top_locations: List[LocationStats] = Field(
        description="Per location breakdown, most sets first",
        default_factory=list,
    )

    @field_validator("first_performed", "last_performed", mode="before")
    @classmethod
    def ensure_timezone_aware(cls, value):
        """Convert naive datetimes to timezone-aware datetimes (UTC)"""
        if value is None:
            return None
        if isinstance(value, datetime.datetime) and value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value
