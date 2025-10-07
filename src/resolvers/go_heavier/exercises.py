import datetime
import uuid
from typing import Optional

from src.db import session
from src.models.go_heavier.exercise import Exercise as DBExercise
from src.schemas.go_heavier.exercises import ExerciseRequest


def get_exercise(exercise_id: uuid.UUID) -> Optional[DBExercise]:
    return session.query(DBExercise).filter(DBExercise.id == exercise_id).first()


def get_exercises() -> list[DBExercise]:
    return session.query(DBExercise).all()


def update_exercise(
    exercise_id: uuid.UUID, exercise: ExerciseRequest
) -> Optional[DBExercise]:
    db_exercise = get_exercise(exercise_id)
    if not db_exercise:
        return None

    for field, value in exercise.model_dump().items():
        if value is not None:
            setattr(db_exercise, field, value)

    db_exercise.updated_at = datetime.datetime.now(tz=datetime.timezone.utc)

    session.commit()
    return db_exercise


def create_exercise(exercise: ExerciseRequest) -> DBExercise:
    new_exercise = DBExercise(
        id=uuid.uuid4(),
        name=exercise.name,
        description=exercise.description,
        muscle_group=exercise.muscle_group,
        specific_muscle=exercise.specific_muscle,
        bipedal=exercise.bipedal,
        free_weights=exercise.free_weights,
        created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        updated_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    session.add(new_exercise)
    session.commit()
    return new_exercise


def delete_exercise(exercise_id: uuid.UUID) -> bool:
    exercise = get_exercise(exercise_id)
    if not exercise:
        return False
    session.delete(exercise)
    session.commit()
    return True
