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
    heaviest_weight_kg: float = Field(
        description="The heaviest single weight lifted in the session"
    )

    @field_validator("workout_time", mode="before")
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


class SessionSummary(_BaseSession):
    pass


class SessionResponse(_BaseSession):
    by_exercise: List[SessionExerciseStats] = Field(
        description="Per exercise breakdown, in the order the exercises were performed",
        default_factory=list,
    )
