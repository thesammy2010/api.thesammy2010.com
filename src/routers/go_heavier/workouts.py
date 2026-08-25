import logging
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from src.models.go_heavier.workout import Workout as DBWorkout
from src.resolvers.go_heavier import workouts
from src.resolvers.users import require_editor, require_viewer
from src.schemas.go_heavier.workout_stats import (
    WorkoutStatsRequest,
    WorkoutStatsResponse,
)
from src.schemas.go_heavier.workouts import (
    CreateWorkoutsRequest,
    ListWorkoutsRequest,
    UpdateWorkoutRequest,
    WorkoutResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/go-heavier", tags=["workouts"])


@router.get(
    "/workouts/stats",
    response_model=WorkoutStatsResponse,
    dependencies=[Depends(require_viewer)],
)
async def get_workout_stats(
    request: Annotated[WorkoutStatsRequest, Query()],
) -> WorkoutStatsResponse:
    """Aggregates across workouts (sets) rather than a single one.

    Every filter is optional and they combine, so this one endpoint covers
    everything, one gym, one exercise, or a date range. A session is one
    distinct `workout_time`.
    """
    return workouts.get_workout_stats(request=request)


# Declared after /workouts/stats so that "stats" is not read as a workout id
@router.get(
    "/workouts/{workout_id}",
    response_model=WorkoutResponse,
    dependencies=[Depends(require_viewer)],
)
async def get_workout(workout_id: str) -> Optional[DBWorkout]:
    """A single set by id."""
    try:
        workout_uuid = uuid.UUID(workout_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for workout id"},
        )
    workout = workouts.get_workout(workout_uuid)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@router.get(
    "/workouts",
    response_model=List[WorkoutResponse],
    dependencies=[Depends(require_viewer)],
)
async def get_workouts(
    request: Annotated[ListWorkoutsRequest, Query()],
) -> List[DBWorkout]:
    """Lists sets, optionally filtered."""
    return workouts.get_workouts(request=request)


@router.post(
    "/workouts",
    response_model=List[WorkoutResponse],
    status_code=201,
    dependencies=[Depends(require_editor)],
)
async def create_workout(
    workouts_: CreateWorkoutsRequest,
) -> Optional[List[DBWorkout]]:
    """Logs one or more sets. The request takes a list, so the response is
    the list that was created."""
    try:
        new_workouts = workouts.create_workouts(workouts=workouts_)
        return new_workouts
    except Exception as e:
        logger.error(f"Error creating workout: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put(
    "/workouts/{workout_id}",
    response_model=WorkoutResponse,
    dependencies=[Depends(require_editor)],
)
def update_workout(
    workout_id: Annotated[str, uuid.UUID],
    workout: UpdateWorkoutRequest,
) -> Optional[DBWorkout]:
    """Replaces a set's fields."""
    try:
        workout_uuid = uuid.UUID(workout_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for workout id"},
        )
    updated_workout = workouts.update_workout(workout_id=workout_uuid, workout=workout)
    if not updated_workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return updated_workout


@router.delete(
    "/workouts/{workout_id}",
    status_code=204,
    dependencies=[Depends(require_editor)],
)
async def delete_workout(
    workout_id: Annotated[str, uuid.UUID],
) -> Response:
    """Deletes a set."""
    try:
        workout_uuid = uuid.UUID(workout_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for workout id"},
        )
    success = workouts.delete_workout(workout_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Workout not found")
    return Response(status_code=204)
