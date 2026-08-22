import uuid
from typing import List, Optional

from sqlalchemy import desc, distinct, func

from src.config import Config
from src.db import session
from src.models.go_heavier import Exercise as DBExercise
from src.models.go_heavier import Location as DBLocation
from src.models.go_heavier import Session as DBSession
from src.models.go_heavier import Workout as DBWorkout
from src.schemas.go_heavier.workout_stats import (
    ExerciseBreakdown,
    LocationBreakdown,
    WorkoutStatsRequest,
    WorkoutStatsResponse,
)
from src.schemas.go_heavier.workouts import (
    CreateWorkoutsRequest,
    ListWorkoutsRequest,
    UpdateWorkoutRequest,
)


def get_workout(workout_id: uuid.UUID) -> Optional[DBWorkout]:
    return session.query(DBWorkout).filter(DBWorkout.id == workout_id).first()


def get_workouts(request: ListWorkoutsRequest) -> List[DBWorkout]:
    conditions = []
    if request.session_id:
        conditions.append(DBWorkout.session_id == request.session_id)
    if request.exercise_id:
        conditions.append(DBWorkout.exercise_id == request.exercise_id)
    if request.location_id:
        conditions.append(DBSession.location_id == request.location_id)
    if request.after:
        conditions.append(DBSession.workout_time >= request.after)
    if request.before:
        conditions.append(DBSession.workout_time <= request.before)

    query = (
        session.query(DBWorkout)
        .join(DBSession, DBSession.id == DBWorkout.session_id)
        .where(*conditions)
        .order_by(DBSession.workout_time, DBWorkout.exercise_id, DBWorkout.index)
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
                session_id=workout.session_id,  # relationship handled by db
                exercise_id=workout.exercise_id,  # relationship handled by db
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


def get_workout_stats(request: WorkoutStatsRequest) -> WorkoutStatsResponse:
    """Aggregate across workouts.

    A session is one distinct ``workout_time``, since every set logged in a
    session shares that session's timestamp.
    """
    conditions = []
    if request.location_id:
        conditions.append(DBSession.location_id == request.location_id)
    if request.exercise_id:
        conditions.append(DBWorkout.exercise_id == request.exercise_id)
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
        first_workout,
        last_workout,
        distinct_locations,
        distinct_exercises,
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
            func.count(distinct(DBWorkout.exercise_id)),
        )
        .join(DBSession, DBSession.id == DBWorkout.session_id)
        .filter(*conditions)
        .one()
    )

    # Averaged per session rather than derived from the totals: the distinct
    # exercise count spans every session, so it cannot be divided down.
    exercises_per_session = (
        session.query(func.count(distinct(DBWorkout.exercise_id)).label("exercises"))
        .join(DBSession, DBSession.id == DBWorkout.session_id)
        .filter(*conditions)
        .group_by(DBWorkout.session_id)
        .subquery()
    )
    average_exercises_per_session = session.query(
        func.avg(exercises_per_session.c.exercises)
    ).scalar()

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

    top_exercises = (
        session.query(
            DBWorkout.exercise_id,
            DBExercise.name,
            func.count(distinct(DBWorkout.session_id)).label("sessions"),
            func.count(DBWorkout.id).label("sets"),
            func.sum(DBWorkout.repetitions).label("repetitions"),
            volume.label("volume_kg"),
        )
        .join(DBSession, DBSession.id == DBWorkout.session_id)
        .join(DBExercise, DBExercise.id == DBWorkout.exercise_id)
        .filter(*conditions)
        .group_by(DBWorkout.exercise_id, DBExercise.name)
        .order_by(desc("sets"), DBExercise.name)
        .limit(request.top_exercises)
        .all()
    )

    total_repetitions = total_repetitions or 0
    return WorkoutStatsResponse(
        sessions=sessions,
        first_workout=first_workout,
        last_workout=last_workout,
        total_sets=total_sets,
        total_repetitions=total_repetitions,
        total_volume_kg=round(total_volume_kg or 0.0, 2),
        heaviest_weight_kg=heaviest_weight_kg,
        average_sets_per_session=round(total_sets / sessions, 2) if sessions else 0.0,
        average_exercises_per_session=round(
            float(average_exercises_per_session or 0.0), 2
        ),
        average_repetitions_per_set=(
            round(total_repetitions / total_sets, 2) if total_sets else 0.0
        ),
        distinct_locations=distinct_locations,
        distinct_exercises=distinct_exercises,
        top_locations=[
            LocationBreakdown(
                location_id=row.location_id,
                name=row.name,
                sessions=row.sessions,
                sets=row.sets,
                repetitions=row.repetitions or 0,
                volume_kg=round(row.volume_kg or 0.0, 2),
            )
            for row in top_locations
        ],
        top_exercises=[
            ExerciseBreakdown(
                exercise_id=row.exercise_id,
                name=row.name,
                sessions=row.sessions,
                sets=row.sets,
                repetitions=row.repetitions or 0,
                volume_kg=round(row.volume_kg or 0.0, 2),
            )
            for row in top_exercises
        ],
    )
