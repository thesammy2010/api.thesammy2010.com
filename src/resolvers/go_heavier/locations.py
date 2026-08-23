import datetime
import uuid
from typing import List, Optional

from sqlalchemy import desc, distinct, func

from src.db import session
from src.models.go_heavier.exercise import Exercise as DBExercise
from src.models.go_heavier.location import Location as DBLocation
from src.models.go_heavier.session import Session as DBSession
from src.models.go_heavier.workout import Workout as DBWorkout
from src.schemas.go_heavier.location_stats import (
    ExerciseStats,
    LocationStatsRequest,
    LocationStatsResponse,
)
from src.schemas.go_heavier.locations import LocationRequest


def get_location(location_id: uuid.UUID) -> Optional[DBLocation]:
    return session.query(DBLocation).filter(DBLocation.id == location_id).first()


def get_locations() -> List[DBLocation]:
    return session.query(DBLocation).all()


def update_location(
    location_id: uuid.UUID, location: LocationRequest
) -> Optional[DBLocation]:
    db_location = get_location(location_id)
    if not db_location:
        return None

    for field, value in location.model_dump().items():
        if value is not None:
            setattr(db_location, field, value)

    db_location.updated_at = datetime.datetime.now(tz=datetime.timezone.utc)

    session.commit()
    return db_location


def create_location(location: LocationRequest) -> DBLocation:
    new_location = DBLocation(
        id=uuid.uuid4(),
        name=location.name,
        description=location.description,
        logo_url=location.logo_url,
        address_line1=location.address_line1,
        address_line2=location.address_line2,
        address_city=location.address_city,
        address_postal_code=location.address_postal_code,
        address_country_iso3=location.address_country_iso3,
        created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        updated_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    session.add(new_location)
    session.commit()
    return new_location


def delete_location(location_id: uuid.UUID) -> bool:
    location = get_location(location_id)
    if not location:
        return False
    session.delete(location)
    session.commit()
    return True


def get_location_stats(
    location_id: uuid.UUID, request: LocationStatsRequest
) -> Optional[LocationStatsResponse]:
    """Aggregate a location's workout history.

    A visit is one distinct ``workout_time``, since every set logged in a
    session shares that session's timestamp.
    """
    location = get_location(location_id)
    if not location:
        return None

    conditions = [DBSession.location_id == location_id]
    if request.after:
        conditions.append(DBSession.workout_time >= request.after)
    if request.before:
        conditions.append(DBSession.workout_time <= request.before)

    volume = func.sum(DBWorkout.weight_kg * DBWorkout.repetitions)
    (
        visits,
        total_sets,
        total_repetitions,
        total_volume_kg,
        heaviest_weight_kg,
        first_visit,
        last_visit,
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
            func.count(distinct(DBWorkout.exercise_id)),
        )
        .join(DBSession, DBSession.id == DBWorkout.session_id)
        .filter(*conditions)
        .one()
    )

    # Averaged per visit rather than derived from the totals: a location's
    # distinct exercise count spans every visit, so it cannot be divided down.
    exercises_per_visit = (
        session.query(func.count(distinct(DBWorkout.exercise_id)).label("exercises"))
        .join(DBSession, DBSession.id == DBWorkout.session_id)
        .filter(*conditions)
        .group_by(DBWorkout.session_id)
        .subquery()
    )
    average_exercises_per_visit = session.query(
        func.avg(exercises_per_visit.c.exercises)
    ).scalar()

    top_exercises = (
        session.query(
            DBWorkout.exercise_id,
            DBExercise.name,
            func.count(distinct(DBWorkout.session_id)).label("visits"),
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

    return LocationStatsResponse(
        location_id=location.id,
        name=location.name,
        visits=visits,
        first_visit=first_visit,
        last_visit=last_visit,
        total_sets=total_sets,
        total_repetitions=total_repetitions or 0,
        total_volume_kg=round(total_volume_kg or 0.0, 2),
        heaviest_weight_kg=heaviest_weight_kg,
        average_sets_per_visit=round(total_sets / visits, 2) if visits else 0.0,
        average_exercises_per_visit=round(float(average_exercises_per_visit or 0.0), 2),
        distinct_exercises=distinct_exercises,
        top_exercises=[
            ExerciseStats(
                exercise_id=row.exercise_id,
                name=row.name,
                visits=row.visits,
                sets=row.sets,
                repetitions=row.repetitions or 0,
                volume_kg=round(row.volume_kg or 0.0, 2),
            )
            for row in top_exercises
        ],
    )
