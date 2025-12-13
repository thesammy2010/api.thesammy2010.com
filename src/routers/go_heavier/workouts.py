import logging
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, HTTPException, Query, Response

from src.models.go_heavier.workout import Workout as DBWorkout
from src.resolvers.go_heavier import workouts
from src.schemas.go_heavier.workouts import (
    CreateWorkoutsRequest,
    ListWorkoutsRequest,
    UpdateWorkoutRequest,
    WorkoutResponse,
)

router = APIRouter(prefix="/go-heavier", tags=["workouts"])


@router.get("/workouts/{workout_id}", response_model=WorkoutResponse)
async def get_workout(workout_id: str) -> Optional[DBWorkout]:
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


@router.get("/workouts", response_model=List[WorkoutResponse])
async def get_workouts(
    request: Annotated[ListWorkoutsRequest, Query()],
) -> List[DBWorkout]:
    return workouts.get_workouts(request=request)


@router.post("/workouts", response_model=WorkoutResponse)
async def create_workout(
    workouts_: CreateWorkoutsRequest,
) -> Optional[List[DBWorkout]]:
    try:
        new_workouts = workouts.create_workouts(workouts=workouts_)
        return new_workouts
    except Exception as e:
        logging.error(f"Error creating workout: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# update workout
@router.put("/workouts/{workout_id}", response_model=WorkoutResponse)
def update_workout(
    workout_id: Annotated[str, uuid.UUID],
    workout: UpdateWorkoutRequest,
) -> Optional[DBWorkout]:
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


# delete workout
@router.delete("/workouts/{workout_id}", response_model=WorkoutResponse)
async def delete_workout(
    workout_id: Annotated[str, uuid.UUID],
) -> Response:
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
