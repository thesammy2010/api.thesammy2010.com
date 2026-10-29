import datetime
import uuid
from typing import List, Optional, Sequence, Tuple

from sqlalchemy import select
from sqlalchemy.orm import defer

from src.config import Config
from src.db import session
from src.models.go_heavier import HealthDay as DBHealthDay
from src.models.go_heavier import HealthWorkout as DBHealthWorkout
from src.models.go_heavier import Session as DBSession
from src.schemas.go_heavier.health import (
    ListHealthDaysRequest,
    ListHealthWorkoutsRequest,
    PutHealthDayRequest,
    PutHealthWorkoutRequest,
)

# A session's workout_time is when it was logged as starting, normally a
# few minutes before the watch was started but sometimes over an hour, so
# it may fall anywhere from this long before the workout starts to when it
# ends.
MATCH_WINDOW_BEFORE = datetime.timedelta(hours=2)
# Shorter than this is a workout started by accident and stopped again.
MIN_MATCH_DURATION = datetime.timedelta(minutes=5)


def long_enough(duration_seconds: float) -> bool:
    """Whether a workout is long enough to be matched to a session at all."""
    return datetime.timedelta(seconds=duration_seconds) >= MIN_MATCH_DURATION


def could_match(
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    duration_seconds: float,
    workout_time: datetime.datetime,
) -> bool:
    """Whether a session logged at workout_time could be the one a workout
    was recorded during."""
    if not long_enough(duration_seconds):
        return False
    return start_time - MATCH_WINDOW_BEFORE <= workout_time <= end_time


def nearest(
    start_time: datetime.datetime,
    candidates: Sequence[Tuple[uuid.UUID, datetime.datetime]],
) -> Optional[uuid.UUID]:
    """The candidate whose time is closest to the workout's start. The id
    breaks ties, so the choice never depends on the order rows came back
    in."""
    if not candidates:
        return None
    return min(candidates, key=lambda c: (abs(c[1] - start_time), str(c[0])))[0]


class SessionNotFound(LookupError):
    """Raised when linking a workout to a session that does not exist."""


class SessionAlreadyLinked(ValueError):
    """Raised when linking a workout to a session another workout has."""

    def __init__(self, workout_id: uuid.UUID) -> None:
        self.workout_id = workout_id
        super().__init__(f"The session is already linked to workout {workout_id}")


# MARK: Workouts


def get_workouts(request: ListHealthWorkoutsRequest) -> List[DBHealthWorkout]:
    conditions = []
    if request.session_id:
        conditions.append(DBHealthWorkout.session_id == request.session_id)
    if request.after:
        conditions.append(DBHealthWorkout.start_time >= request.after)
    if request.before:
        conditions.append(DBHealthWorkout.start_time <= request.before)

    return (
        session.query(DBHealthWorkout)
        # Listed without the readings, which are most of each row.
        .options(defer(DBHealthWorkout.heart_rate))
        .filter(*conditions)
        .order_by(DBHealthWorkout.start_time, DBHealthWorkout.id)
        .limit(Config.DEFAULT_DB_PAGE_SIZE)
        .offset(request.offset)
        .all()
    )


def get_workout(workout_id: uuid.UUID) -> Optional[DBHealthWorkout]:
    return (
        session.query(DBHealthWorkout).filter(DBHealthWorkout.id == workout_id).first()
    )


def put_workout(
    workout_id: uuid.UUID, request: PutHealthWorkoutRequest
) -> DBHealthWorkout:
    """Creates or replaces a workout, then links it to the session it was
    recorded during, unless it was linked by hand."""
    workout = get_workout(workout_id)
    if workout is None:
        workout = DBHealthWorkout(id=workout_id, session_linked_manually=False)
        session.add(workout)

    for field, value in request.model_dump().items():
        setattr(workout, field, value)

    if not workout.session_linked_manually:
        workout.session_id = _match_session(workout)

    session.commit()
    return workout


def _match_session(workout: DBHealthWorkout) -> Optional[uuid.UUID]:
    if not long_enough(workout.duration_seconds):
        return None

    linked_elsewhere = select(DBHealthWorkout.session_id).where(
        DBHealthWorkout.session_id.is_not(None),
        DBHealthWorkout.id != workout.id,
    )
    candidates = (
        session.query(DBSession.id, DBSession.workout_time)
        .filter(
            DBSession.workout_time >= workout.start_time - MATCH_WINDOW_BEFORE,
            DBSession.workout_time <= workout.end_time,
            DBSession.id.not_in(linked_elsewhere),
        )
        .all()
    )
    return nearest(
        workout.start_time, [(row.id, row.workout_time) for row in candidates]
    )


def match_new_session(session_id: uuid.UUID, workout_time: datetime.datetime) -> None:
    """Links a session that has just been created to the workout recorded
    during it, when that workout arrived first. Doesn't commit."""
    candidates = (
        session.query(DBHealthWorkout)
        .options(defer(DBHealthWorkout.heart_rate))
        .filter(
            DBHealthWorkout.session_id.is_(None),
            DBHealthWorkout.session_linked_manually.is_(False),
            DBHealthWorkout.start_time <= workout_time + MATCH_WINDOW_BEFORE,
            DBHealthWorkout.end_time >= workout_time,
        )
        .all()
    )
    matching = [
        workout
        for workout in candidates
        if could_match(
            workout.start_time,
            workout.end_time,
            workout.duration_seconds,
            workout_time,
        )
    ]
    if not matching:
        return

    # Nearest start to the session's time, the same measure as the other way.
    chosen = min(matching, key=lambda w: (abs(w.start_time - workout_time), str(w.id)))
    chosen.session_id = session_id


def link_workout(
    workout_id: uuid.UUID, session_id: Optional[uuid.UUID]
) -> Optional[DBHealthWorkout]:
    """Links a workout to a session by hand, or to none. Automatic matching
    leaves it alone from then on."""
    workout = get_workout(workout_id)
    if workout is None:
        return None

    if session_id is not None:
        if not session.query(DBSession).filter(DBSession.id == session_id).first():
            raise SessionNotFound(f"No session with id {session_id}")
        other = (
            session.query(DBHealthWorkout.id)
            .filter(
                DBHealthWorkout.session_id == session_id,
                DBHealthWorkout.id != workout_id,
            )
            .first()
        )
        if other:
            raise SessionAlreadyLinked(other.id)

    workout.session_id = session_id
    workout.session_linked_manually = True
    session.commit()
    return workout


# MARK: Days


def get_days(request: ListHealthDaysRequest) -> List[DBHealthDay]:
    conditions = []
    if request.after:
        conditions.append(DBHealthDay.date >= request.after)
    if request.before:
        conditions.append(DBHealthDay.date <= request.before)

    return (
        session.query(DBHealthDay)
        .filter(*conditions)
        .order_by(DBHealthDay.date)
        .limit(Config.DEFAULT_DB_PAGE_SIZE)
        .offset(request.offset)
        .all()
    )


def put_day(date: datetime.date, request: PutHealthDayRequest) -> DBHealthDay:
    """Creates or replaces one day."""
    day = session.query(DBHealthDay).filter(DBHealthDay.date == date).first()
    if day is None:
        day = DBHealthDay(date=date)
        session.add(day)

    for field, value in request.model_dump().items():
        setattr(day, field, value)

    session.commit()
    return day
