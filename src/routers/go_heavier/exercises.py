import logging
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, HTTPException, Response

from src.models.go_heavier.exercise import Exercise as DBExercise
from src.resolvers.go_heavier import exercises
from src.schemas.go_heavier.exercises import ExerciseRequest, ExerciseResponse

router = APIRouter(prefix="/go-heavier", tags=["exercises"])


@router.get("/exercises", response_model=List[ExerciseResponse])
def get_exercises() -> List[DBExercise]:
    return exercises.get_exercises()


@router.get("/exercises/{exercise_id}", response_model=Optional[ExerciseResponse])
async def get_exercise(exercise_id: Annotated[str, uuid.UUID]) -> Optional[DBExercise]:
    try:
        exercise_uuid = uuid.UUID(exercise_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for exercise id"},
        )
    exercise = exercises.get_exercise(exercise_uuid)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise


@router.post("/exercises", response_model=ExerciseResponse)
async def create_exercise(exercise: ExerciseRequest) -> Optional[DBExercise]:
    try:
        new_exercise = exercises.create_exercise(exercise)
        return new_exercise
    except Exception as e:
        logging.error(f"Error creating exercise: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: Annotated[str, uuid.UUID],
    exercise: ExerciseRequest,
) -> Optional[DBExercise]:
    try:
        exercise_uuid = uuid.UUID(exercise_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for exercise id"},
        )
    updated_exercise = exercises.update_exercise(
        exercise_id=exercise_uuid, exercise=exercise
    )
    if not updated_exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return updated_exercise


@router.delete("/exercises/{exercise_id}")
def delete_exercise(exercise_id: Annotated[str, uuid.UUID]) -> Response:
    try:
        exercise_uuid = uuid.UUID(exercise_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for exercise id"},
        )
    if not exercises.delete_exercise(exercise_uuid):
        raise HTTPException(status_code=404, detail="Exercise not found")
    return Response(status_code=204)
