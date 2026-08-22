import datetime
import uuid
from typing import Optional

from sqlalchemy import desc, distinct, func

from src.db import session
from src.models.go_heavier.exercise import Exercise as DBExercise
from src.models.go_heavier.location import Location as DBLocation
from src.models.go_heavier.session import Session as DBSession
from src.models.go_heavier.workout import Workout as DBWorkout
from src.schemas.go_heavier.exercise_stats import (
    ExerciseStatsRequest,
    ExerciseStatsResponse,
    LocationStats,
)
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


def get_exercise_stats(
    exercise_id: uuid.UUID, request: ExerciseStatsRequest
) -> Optional[ExerciseStatsResponse]:
    """Aggregate an exercise's history.

    A session is one distinct ``workout_time``, since every set logged in a
    session shares that session's timestamp.
    """
    exercise = get_exercise(exercise_id)
    if not exercise:
        return None

    conditions = [DBWorkout.exercise_id == exercise_id]
    if request.after:
        conditions.append(DBSession.workout_time >= request.after)
    if request.before:
        conditions.append(DBSession.workout_time <= request.before)

    volume = func.sum(DBWorkout.weight_kg * DBWorkout.repetitions)
    (
        sessions,
        total_sets,
        total_repetitions,
        total_volume_kg,
        heaviest_weight_kg,
        first_performed,
        last_performed,
        distinct_locations,
    ) = (
        session.query(
            func.count(distinct(DBWorkout.session_id)),
            func.count(DBWorkout.id),
            func.sum(DBWorkout.repetitions),
            volume,
            func.max(DBWorkout.weight_kg),
            func.min(DBSession.workout_time),
            func.max(DBSession.workout_time),
            func.count(distinct(DBSession.location_id)),
        )
        .join(DBSession, DBSession.id == DBWorkout.session_id)
        .filter(*conditions)
        .one()
    )

    top_locations = (
        session.query(
            DBSession.location_id,
            DBLocation.name,
            func.count(distinct(DBWorkout.session_id)).label("sessions"),
            func.count(DBWorkout.id).label("sets"),
            func.sum(DBWorkout.repetitions).label("repetitions"),
            volume.label("volume_kg"),
        )
        .join(DBSession, DBSession.id == DBWorkout.session_id)
        .join(DBLocation, DBLocation.id == DBSession.location_id)
        .filter(*conditions)
        .group_by(DBSession.location_id, DBLocation.name)
        .order_by(desc("sets"), DBLocation.name)
        .limit(request.top_locations)
        .all()
    )

    total_repetitions = total_repetitions or 0
    return ExerciseStatsResponse(
        exercise_id=exercise.id,
        name=exercise.name,
        sessions=sessions,
        first_performed=first_performed,
        last_performed=last_performed,
        total_sets=total_sets,
        total_repetitions=total_repetitions,
        total_volume_kg=round(total_volume_kg or 0.0, 2),
        heaviest_weight_kg=heaviest_weight_kg,
        average_sets_per_session=round(total_sets / sessions, 2) if sessions else 0.0,
        average_repetitions_per_set=(
            round(total_repetitions / total_sets, 2) if total_sets else 0.0
        ),
        distinct_locations=distinct_locations,
        top_locations=[
            LocationStats(
                location_id=row.location_id,
                name=row.name,
                sessions=row.sessions,
                sets=row.sets,
                repetitions=row.repetitions or 0,
                volume_kg=round(row.volume_kg or 0.0, 2),
            )
            for row in top_locations
        ],
    )
