import uuid
from typing import List, Optional

from src.config import Config
from src.db import session
from src.models.go_heavier import Workout as DBWorkout
from src.schemas.go_heavier.workouts import (
    CreateWorkoutsRequest,
    ListWorkoutsRequest,
    UpdateWorkoutRequest,
)


def get_workout(workout_id: uuid.UUID) -> Optional[DBWorkout]:
    return session.query(DBWorkout).filter(DBWorkout.id == workout_id).first()


def get_workouts(request: ListWorkoutsRequest) -> List[DBWorkout]:
    conditions = []
    if request.location_id:
        conditions.append(DBWorkout.location_id == request.location_id)
    if request.exercise_id:
        conditions.append(DBWorkout.exercise_id == request.exercise_id)
    if request.after:
        conditions.append(DBWorkout.workout_time >= request.after)
    if request.before:
        conditions.append(DBWorkout.workout_time <= request.before)

    query = (
        session.query(DBWorkout)
        .where(*conditions)
        .order_by(DBWorkout.workout_time, DBWorkout.exercise_id, DBWorkout.index)
        .limit(Config.DEFAULT_DB_PAGE_SIZE)
    )

    if request.page is not None:
        query = query.offset(request.offset)

    return query.all()


def create_workouts(workouts: CreateWorkoutsRequest) -> List[DBWorkout]:
    new_workouts: List[DBWorkout] = []
    for workout in workouts.workouts:
        new_workouts.append(
            DBWorkout(
                location_id=workout.location_id,  # relationship handled by db
                exercise_id=workout.exercise_id,  # relationship handled by db
                workout_time=workout.workout_time,
                index=workout.index,
                repetitions=workout.repetitions,
                weight_kg=workout.weight_kg,
                bar_weight_kg=workout.bar_weight_kg,
                supplementary_weight_kg=workout.supplementary_weight_kg,
                notes=workout.notes,
            )
        )

    session.add_all(new_workouts)
    session.commit()
    return new_workouts


def update_workout(
    workout_id: uuid.UUID, workout: UpdateWorkoutRequest
) -> Optional[DBWorkout]:
    db_workout = session.query(DBWorkout).filter(DBWorkout.id == workout_id).first()
    if not db_workout:
        return None

    for field, value in workout.model_dump().items():
        if value is not None:
            setattr(db_workout, field, value)

    session.commit()
    return db_workout


def delete_workout(workout_id: uuid.UUID) -> Optional[DBWorkout]:
    db_workout = session.query(DBWorkout).filter(DBWorkout.id == workout_id).first()
    if not db_workout:
        return None

    session.delete(db_workout)
    session.commit()
    return db_workout
