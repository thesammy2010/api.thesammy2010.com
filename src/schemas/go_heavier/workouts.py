import math
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from src.schemas.utils import PaginationParams


class _BaseWorkout(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: UUID = Field(
        description="Unique identifier for the session this set belongs to. The "
        "location and the time are on the session",
    )
    exercise_id: UUID = Field(
        description="Unique identifier for this workout exercise",
    )
    index: int = Field(
        description="The index of the set within the workout session",
        gt=0,
        lt=100,
    )
    repetitions: int = Field(
        description="The number of times the workout action was repeated",
        gt=0,
        lt=100,
    )
    weight_kg: float = Field(
        description="The weight used during the workout in kilograms. Negative "
        "for an assisted exercise, where the machine takes weight off the lifter",
        gt=-1000.0,
        lt=1000.0,
    )
    bar_weight_kg: Optional[float] = Field(
        description="The weight of the bar used during the workout in kilograms",
        gt=0.0,
        lt=100.0,
        default=None,
    )
    supplementary_weight_kg: Optional[float] = Field(
        description="The supplementary weight added to the bar during the workout "
        "in kilograms. Negative when it assists rather than loads the lifter",
        gt=-100.0,
        lt=100.0,
        default=None,
    )
    notes: Optional[str] = Field(
        description="Additional notes or comments about the workout",
        max_length=512,
        default=None,
    )

    @field_validator("bar_weight_kg", "supplementary_weight_kg", mode="before")
    @classmethod
    def convert_nan_to_none(cls, value):
        """Convert NaN or 0.0 values to None for optional float fields"""
        if value is None:
            return None
        if isinstance(value, float):
            if math.isnan(value) or value == 0.0:
                return None
        return value


class CreateWorkoutsRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workouts: List[_BaseWorkout] = Field(
        min_length=1,
        max_length=10,
        description="List of workouts to be created",
        default=None,
    )


class UpdateWorkoutRequest(_BaseWorkout):
    pass


class ListWorkoutsRequest(PaginationParams):
    model_config = ConfigDict(from_attributes=True)

    exercise_id: Optional[UUID] = Field(
        description="Only list sets of this exercise",
        default=None,
    )
    location_id: Optional[UUID] = Field(
        description="Only list sets from sessions at this location",
        default=None,
    )
    after: Optional[AwareDatetime] = Field(
        description="Only list sets from sessions at or after this datetime",
        default=None,
    )
    before: Optional[AwareDatetime] = Field(
        description="Only list sets from sessions at or before this datetime",
        default=None,
    )
    session_id: Optional[UUID] = Field(
        description="Only list sets from this session",
        default=None,
    )


class WorkoutResponse(_BaseWorkout):
    id: UUID
    created_at: AwareDatetime
    updated_at: Optional[AwareDatetime]

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def ensure_timezone_aware(cls, value):
        """Convert naive datetimes to timezone-aware datetimes (UTC)"""
        if value is None:
            return None
        if isinstance(value, datetime) and value.tzinfo is None:
            # If naive datetime, assume UTC
            return value.replace(tzinfo=timezone.utc)
        return value
