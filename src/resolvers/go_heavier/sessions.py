import datetime
import logging
import uuid
from typing import List, Optional

import pendulum
from sqlalchemy import distinct, func, select

from src.config import Config
from src.db import session
from src.migration_utils.session_ids import session_id_for
from src.models.go_heavier import Exercise as DBExercise
from src.models.go_heavier import Location as DBLocation
from src.models.go_heavier import Session as DBSession
from src.models.go_heavier import SleepRecord
from src.models.go_heavier import Workout as DBWorkout
from src.schemas.go_heavier.session_stats import (
    SessionHighlight,
    SessionStatsRequest,
    SessionStatsResponse,
    WeekdayStats,
)
from src.schemas.go_heavier.sessions import (
    CreateSessionRequest,
    ListSessionsRequest,
    SessionExerciseStats,
    SessionResponse,
    SessionSummary,
    UpdateSessionRequest,
)

logger = logging.getLogger(__name__)

# A session owns its sets, so the totals are an aggregate over the join.
# The enrichment columns belong to the session itself, not the sets, but
# still have to be listed (and grouped by) here since they're selected
# alongside an aggregate.
_ENRICHMENT_COLUMNS = (
    DBSession.duration_minutes,
    DBSession.calories_burned_kcal,
    DBSession.took_preworkout,
    DBSession.went_to_office,
    DBSession.sleep_hours,
    DBSession.bed_time,
    DBSession.sleep_score,
)
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
    *_ENRICHMENT_COLUMNS,
)
_GROUP_BY = (
    DBSession.id,
    DBSession.workout_time,
    DBSession.location_id,
    DBLocation.name,
    *_ENRICHMENT_COLUMNS,
)


def _summary_query():
    return (
        session.query(*_SUMMARY_COLUMNS)
        .join(DBLocation, DBLocation.id == DBSession.location_id)
        # Outer, so that a session created before anything is logged against
        # it still reads back, with totals of zero rather than not at all.
        .outerjoin(DBWorkout, DBWorkout.session_id == DBSession.id)
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
        duration_minutes=row.duration_minutes,
        calories_burned_kcal=row.calories_burned_kcal,
        took_preworkout=row.took_preworkout,
        went_to_office=row.went_to_office,
        sleep_hours=row.sleep_hours,
        bed_time=row.bed_time,
        sleep_score=row.sleep_score,
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


# Postgres numbers the week from Sunday, and a training log reads Monday first.
_WEEKDAY_NAMES = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    0: "Sunday",
}
_WEEKDAY_ORDER = [1, 2, 3, 4, 5, 6, 0]


def _stats_conditions(request: SessionStatsRequest) -> list:
    conditions = []
    if request.location_id:
        conditions.append(DBSession.location_id == request.location_id)
    if request.exercise_id:
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

    return conditions


def _highlight(row) -> SessionHighlight:
    return SessionHighlight(
        id=row.id,
        workout_time=row.workout_time,
        location=row.location,
        sets=row.sets,
        volume_kg=round(row.volume_kg or 0.0, 2),
    )


def get_session_stats(request: SessionStatsRequest) -> SessionStatsResponse:
    """Aggregate across sessions, rather than within one."""
    conditions = _stats_conditions(request)

    # The averages are per session, so they aggregate over the per session
    # totals rather than over the sets directly.
    per_session = _summary_query().filter(*conditions).subquery()
    (
        sessions,
        first_session,
        last_session,
        average_sets,
        average_exercises,
        average_repetitions,
        average_volume,
    ) = session.query(
        func.count(per_session.c.id),
        func.min(per_session.c.workout_time),
        func.max(per_session.c.workout_time),
        func.avg(per_session.c.sets),
        func.avg(per_session.c.exercises),
        func.avg(per_session.c.repetitions),
        func.avg(per_session.c.volume_kg),
    ).one()

    weekday = func.extract(
        "dow", func.timezone("Europe/London", per_session.c.workout_time)
    ).label("weekday")
    by_weekday = {
        int(row.weekday): row
        for row in session.query(
            weekday,
            func.count(per_session.c.id).label("sessions"),
            func.sum(per_session.c.sets).label("sets"),
            func.sum(per_session.c.volume_kg).label("volume_kg"),
        )
        .group_by(weekday)
        .all()
    }

    return SessionStatsResponse(
        sessions=sessions,
        first_session=first_session,
        last_session=last_session,
        average_sets_per_session=round(float(average_sets or 0.0), 2),
        average_exercises_per_session=round(float(average_exercises or 0.0), 2),
        average_repetitions_per_session=round(float(average_repetitions or 0.0), 2),
        average_volume_kg_per_session=round(float(average_volume or 0.0), 2),
        **_gaps_between(conditions),
        busiest_session=_top_session(conditions, func.count(DBWorkout.id)),
        heaviest_session=_top_session(
            conditions, func.sum(DBWorkout.weight_kg * DBWorkout.repetitions)
        ),
        by_weekday=[
            WeekdayStats(
                weekday=_WEEKDAY_NAMES[day],
                sessions=by_weekday[day].sessions,
                sets=by_weekday[day].sets or 0,
                volume_kg=round(by_weekday[day].volume_kg or 0.0, 2),
            )
            for day in _WEEKDAY_ORDER
            if day in by_weekday
        ],
    )


def _top_session(conditions: list, ordering) -> Optional[SessionHighlight]:
    row = (
        _summary_query().filter(*conditions).order_by(ordering.desc()).limit(1).first()
    )

    return _highlight(row) if row else None


def _gaps_between(conditions: list) -> dict:
    """The mean and longest gap between consecutive sessions, in days.

    Computed over the session times rather than in SQL: there is one row per
    session, the same filters bound it, and the arithmetic reads more plainly
    here than as a window function nested two subqueries deep.
    """
    times = [
        row.workout_time
        for row in session.query(DBSession.workout_time)
        .filter(*conditions)
        .order_by(DBSession.workout_time)
        .all()
    ]
    if len(times) < 2:
        return {"average_days_between_sessions": None, "longest_gap_days": None}

    gaps = [
        (later - earlier).total_seconds() / 86400.0
        for earlier, later in zip(times, times[1:])
    ]

    return {
        "average_days_between_sessions": round(sum(gaps) / len(gaps), 2),
        "longest_gap_days": round(max(gaps), 2),
    }


class LocationNotFound(LookupError):
    """Raised when a session is created against a location that does not exist."""


class SessionAlreadyExists(ValueError):
    """Raised when a session has already been logged for that place and time.

    Carries the existing id, since the caller almost certainly wants to log
    against it rather than create another one.
    """

    def __init__(self, session_id: uuid.UUID) -> None:
        self.session_id = session_id
        super().__init__(f"A session already exists with id {session_id}")


def _find_matching_sleep_record(
    workout_time: datetime.datetime,
) -> Optional[SleepRecord]:
    """The most recent not-yet-matched sleep record that woke on the same
    UK calendar date as the session - "last night's sleep" pairs with
    "today's gym session", even when bed_time was technically the day
    before."""
    session_date = pendulum.instance(workout_time).in_tz("Europe/London").date()
    wake_date = func.date(func.timezone("Europe/London", SleepRecord.wake_time))

    return (
        session.query(SleepRecord)
        .filter(SleepRecord.matched_session_id.is_(None), wake_date == session_date)
        .order_by(SleepRecord.wake_time.desc())
        .first()
    )


def create_session(request: CreateSessionRequest) -> SessionResponse:
    """Create a session to log sets against.

    The id is derived exactly as the sheet load derives it, so that a session
    created here and the same visit arriving from the sheet are one row rather
    than two competing for the unique constraint on the location and the time.

    If a sleep record has already arrived for that day (see
    routers.health.receive_sleep_export), it's matched onto the new session
    automatically rather than requiring a separate PATCH.
    """
    location = (
        session.query(DBLocation).filter(DBLocation.id == request.location_id).first()
    )
    if not location:
        raise LocationNotFound(f"No location with id {request.location_id}")

    session_id = session_id_for(
        location_id=request.location_id, workout_time=request.workout_time
    )
    if session.query(DBSession).filter(DBSession.id == session_id).first():
        raise SessionAlreadyExists(session_id)

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    db_session = DBSession(
        id=session_id,
        location_id=request.location_id,
        workout_time=request.workout_time,
        created_at=now,
        updated_at=now,
    )
    session.add(db_session)

    sleep_record = _find_matching_sleep_record(request.workout_time)
    if sleep_record:
        db_session.bed_time = sleep_record.bed_time
        db_session.sleep_hours = sleep_record.sleep_hours
        db_session.sleep_score = sleep_record.sleep_score
        sleep_record.matched_session_id = session_id

    session.commit()

    return get_session(session_id=session_id)


def update_session(
    session_id: uuid.UUID, request: UpdateSessionRequest
) -> Optional[SessionResponse]:
    """Sets the enrichment fields given on the session, leaving any not
    given untouched - a PATCH, not a replace."""
    db_session = session.query(DBSession).filter(DBSession.id == session_id).first()
    if not db_session:
        return None

    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(db_session, field, value)
    session.commit()

    return get_session(session_id=session_id)


def delete_session(session_id: uuid.UUID) -> bool:
    """Delete a session and every set logged against it.

    The sets belong to the session and are meaningless without it, since the
    location and the time they were performed at live on the session.
    """
    db_session = session.query(DBSession).filter(DBSession.id == session_id).first()
    if not db_session:
        return False

    try:
        sets = (
            session.query(DBWorkout)
            .filter(DBWorkout.session_id == session_id)
            .delete(synchronize_session=False)
        )
        session.delete(db_session)
        session.commit()
    except Exception:
        # The session is shared across requests, so it must not be left dirty
        session.rollback()
        raise

    logger.info(f"Deleted session {session_id} and the {sets} sets logged against it")
    return True
