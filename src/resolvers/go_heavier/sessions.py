import uuid
from typing import List, Optional

from sqlalchemy import distinct, func, select

from src.config import Config
from src.db import session
from src.models.go_heavier import Exercise as DBExercise
from src.models.go_heavier import Location as DBLocation
from src.models.go_heavier import Session as DBSession
from src.models.go_heavier import Workout as DBWorkout
from src.schemas.go_heavier.sessions import (
    ListSessionsRequest,
    SessionExerciseStats,
    SessionResponse,
    SessionSummary,
)

# A session owns its sets, so the totals are an aggregate over the join.
_SUMMARY_COLUMNS = (
    DBSession.id,
    DBSession.workout_time,
    DBSession.location_id,
    DBLocation.name.label("location"),
    func.count(DBWorkout.id).label("sets"),
    func.count(distinct(DBWorkout.exercise_id)).label("exercises"),
    func.sum(DBWorkout.repetitions).label("repetitions"),
    func.sum(DBWorkout.weight_kg * DBWorkout.repetitions).label("volume_kg"),
    func.max(DBWorkout.weight_kg).label("heaviest_weight_kg"),
)
_GROUP_BY = (
    DBSession.id,
    DBSession.workout_time,
    DBSession.location_id,
    DBLocation.name,
)


def _summary_query():
    return (
        session.query(*_SUMMARY_COLUMNS)
        .join(DBLocation, DBLocation.id == DBSession.location_id)
        .join(DBWorkout, DBWorkout.session_id == DBSession.id)
        .group_by(*_GROUP_BY)
    )


def _to_summary(row) -> SessionSummary:
    return SessionSummary(
        id=row.id,
        workout_time=row.workout_time,
        location_id=row.location_id,
        location=row.location,
        sets=row.sets,
        exercises=row.exercises,
        repetitions=row.repetitions or 0,
        volume_kg=round(row.volume_kg or 0.0, 2),
        heaviest_weight_kg=row.heaviest_weight_kg,
    )


def get_sessions(request: ListSessionsRequest) -> List[SessionSummary]:
    """List sessions, most recent first."""
    conditions = []
    if request.location_id:
        conditions.append(DBSession.location_id == request.location_id)
    if request.exercise_id:
        # Select the sessions that included the exercise, but still total up
        # every set in them rather than only that exercise's sets.
        conditions.append(
            DBSession.id.in_(
                select(DBWorkout.session_id).filter(
                    DBWorkout.exercise_id == request.exercise_id
                )
            )
        )
    if request.after:
        conditions.append(DBSession.workout_time >= request.after)
    if request.before:
        conditions.append(DBSession.workout_time <= request.before)

    rows = (
        _summary_query()
        .filter(*conditions)
        .order_by(DBSession.workout_time.desc())
        .limit(Config.DEFAULT_DB_PAGE_SIZE)
        .offset(request.offset)
        .all()
    )

    return [_to_summary(row) for row in rows]


def get_session(session_id: uuid.UUID) -> Optional[SessionResponse]:
    """Return one session with its per exercise breakdown."""
    summary = _summary_query().filter(DBSession.id == session_id).first()
    if not summary:
        return None

    by_exercise = (
        session.query(
            DBWorkout.exercise_id,
            DBExercise.name,
            func.count(DBWorkout.id).label("sets"),
            func.sum(DBWorkout.repetitions).label("repetitions"),
            func.sum(DBWorkout.weight_kg * DBWorkout.repetitions).label("volume_kg"),
            func.max(DBWorkout.weight_kg).label("heaviest_weight_kg"),
            func.min(DBWorkout.index).label("first_set"),
        )
        .join(DBExercise, DBExercise.id == DBWorkout.exercise_id)
        .filter(DBWorkout.session_id == session_id)
        .group_by(DBWorkout.exercise_id, DBExercise.name)
        .order_by("first_set", DBExercise.name)
        .all()
    )

    return SessionResponse(
        **_to_summary(summary).model_dump(),
        by_exercise=[
            SessionExerciseStats(
                exercise_id=row.exercise_id,
                name=row.name,
                sets=row.sets,
                repetitions=row.repetitions or 0,
                volume_kg=round(row.volume_kg or 0.0, 2),
                heaviest_weight_kg=row.heaviest_weight_kg,
            )
            for row in by_exercise
        ],
    )
