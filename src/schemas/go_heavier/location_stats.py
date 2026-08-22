"""Schemas for the aggregated view of a location's workout history."""

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


class LocationStatsRequest(BaseModel):
    """Query parameters for narrowing a location's stats."""

    model_config = ConfigDict(from_attributes=True)

    after: Optional[AwareDatetime] = Field(
        description="Only count workouts performed at or after this datetime",
        default=None,
    )
    before: Optional[AwareDatetime] = Field(
        description="Only count workouts performed at or before this datetime",
        default=None,
    )
    top_exercises: int = Field(
        description="How many exercises to include in the breakdown, most sets first",
        default=5,
        ge=1,
        le=25,
    )


class ExerciseStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exercise_id: UUID = Field(description="Unique identifier for the exercise")
    name: str = Field(description="Name of the exercise")
    visits: int = Field(description="Number of visits that included this exercise")
    sets: int = Field(description="Number of sets of this exercise at this location")
    repetitions: int = Field(description="Total repetitions across those sets")
    volume_kg: float = Field(
        description="Total weight moved, the sum of weight_kg multiplied by repetitions"
    )


class LocationStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location_id: UUID = Field(description="Unique identifier for the location")
    name: str = Field(description="Name of the location")
    visits: int = Field(
        description="Number of distinct workout sessions logged at this location"
    )
    first_visit: Optional[AwareDatetime] = Field(
        description="Time of the earliest workout at this location", default=None
    )
    last_visit: Optional[AwareDatetime] = Field(
        description="Time of the most recent workout at this location", default=None
    )
    total_sets: int = Field(description="Number of sets logged at this location")
    total_repetitions: int = Field(
        description="Total repetitions across every set at this location"
    )
    total_volume_kg: float = Field(
        description="Total weight moved, the sum of weight_kg multiplied by repetitions"
    )
    heaviest_weight_kg: Optional[float] = Field(
        description="The heaviest single weight lifted at this location", default=None
    )
    average_sets_per_visit: float = Field(
        description="Mean number of sets per visit, 0 when there are no visits"
    )
    average_exercises_per_visit: float = Field(
        description="Mean number of different exercises performed in a single visit, "
        "0 when there are no visits"
    )
    distinct_exercises: int = Field(
        description="Number of different exercises performed at this location"
    )
    top_exercises: List[ExerciseStats] = Field(
        description="Per exercise breakdown, most sets first",
        default_factory=list,
    )

    @field_validator("first_visit", "last_visit", mode="before")
    @classmethod
    def ensure_timezone_aware(cls, value):
        """Convert naive datetimes to timezone-aware datetimes (UTC)"""
        if value is None:
            return None
        if isinstance(value, datetime.datetime) and value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value
