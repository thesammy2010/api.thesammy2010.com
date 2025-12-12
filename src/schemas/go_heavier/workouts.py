from typing import Annotated, List, Optional
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from src.schemas.utils import PaginationParams


class _BaseWorkout(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location_id: UUID = Field(
        description="Unique identifier for this workout location",
        min_length=32,
        max_length=36,
        nullable=False,
    )
    exercise_id: UUID = Field(
        description="Unique identifier for this workout exercise",
        min_length=32,
        max_length=36,
        nullable=False,
    )
    workout_time: AwareDatetime = Field(
        description="The date and time when the workout was performed",
        nullable=False,
        default=None,
    )
    index: int = Field(
        description="The index of the set within the workout session",
        nullable=False,
        gt=0,
        lt=10,
    )
    repetitions: int = Field(
        description="The number of times the workout action was repeated",
        nullable=False,
        gt=0,
        lt=100,
    )
    weight_kg: float = Field(
        description="The weight used during the workout in kilograms",
        nullable=False,
        gt=0.0,
        lt=1000.0,
    )
    bar_weight_kg: Optional[float] = Field(
        description="The weight of the bar used during the workout in kilograms",
        nullable=True,
        gt=0.0,
        lt=100.0,
        default=0.0,
    )
    supplementary_weight_kg: Optional[float] = Field(
        description="The supplementary weight added to the bar during the workout in kilograms",
        nullable=True,
        gt=0.0,
        lt=100.0,
        default=0.0,
    )
    notes: Optional[str] = Field(
        description="Additional notes or comments about the workout",
        max_length=512,
        nullable=True,
        default=None,
    )


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
    exercise_id: Optional[
        Annotated[
            UUID,
            Field(
                description="Unique identifier for filtering workouts by exercise",
                min_length=32,
                max_length=36,
                nullable=True,
                default=None,
            ),
        ]
    ] = None
    location_id: Optional[
        Annotated[
            UUID,
            Field(
                description="Unique identifier for filtering workouts by location",
                min_length=32,
                max_length=36,
                nullable=True,
                default=None,
            ),
        ]
    ] = None
    after: Optional[
        Annotated[
            AwareDatetime,
            Field(
                description="Filter workouts created after this datetime",
                nullable=True,
                default=None,
            ),
        ]
    ] = None
    before: Optional[
        Annotated[
            AwareDatetime,
            Field(
                description="Filter workouts created before this datetime",
                nullable=True,
                default=None,
            ),
        ]
    ] = None


class WorkoutResponse(_BaseWorkout):
    id: UUID
    created_at: AwareDatetime
    updated_at: Optional[AwareDatetime]
