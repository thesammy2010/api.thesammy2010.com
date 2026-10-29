import datetime
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query

from src.models.go_heavier import HealthDay as DBHealthDay
from src.models.go_heavier import HealthWorkout as DBHealthWorkout
from src.resolvers.go_heavier import health
from src.resolvers.go_heavier.health import SessionAlreadyLinked, SessionNotFound
from src.resolvers.users import require_editor, require_viewer
from src.schemas.go_heavier.health import (
    HealthDayResponse,
    HealthWorkoutResponse,
    HealthWorkoutSummary,
    LinkHealthWorkoutRequest,
    ListHealthDaysRequest,
    ListHealthWorkoutsRequest,
    PutHealthDayRequest,
    PutHealthWorkoutRequest,
)

router = APIRouter(prefix="/go-heavier/health", tags=["health"])


def _workout_uuid(workout_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(workout_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for workout id"},
        )


@router.get(
    "/workouts",
    response_model=List[HealthWorkoutSummary],
    dependencies=[Depends(require_viewer)],
)
async def get_workouts(
    request: Annotated[ListHealthWorkoutsRequest, Query()],
) -> List[DBHealthWorkout]:
    """Lists workouts oldest first, without their heart rate readings."""
    return health.get_workouts(request=request)


@router.get(
    "/workouts/{workout_id}",
    response_model=HealthWorkoutResponse,
    dependencies=[Depends(require_viewer)],
)
async def get_workout(workout_id: Annotated[str, uuid.UUID]) -> DBHealthWorkout:
    """One workout, with every heart rate reading."""
    workout = health.get_workout(_workout_uuid(workout_id))
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@router.put(
    "/workouts/{workout_id}",
    response_model=HealthWorkoutResponse,
    dependencies=[Depends(require_editor)],
)
async def put_workout(
    workout_id: Annotated[str, uuid.UUID], request: PutHealthWorkoutRequest
) -> DBHealthWorkout:
    """Creates or replaces a workout, keyed by its HealthKit UUID, so it can
    be sent any number of times. Unless it was linked by hand, it's linked to
    the session it was recorded during: the one whose workout_time falls
    between two hours before the workout started and when it ended, nearest
    the start, that no other workout has. Workouts under five minutes aren't
    matched."""
    return health.put_workout(_workout_uuid(workout_id), request)


@router.patch(
    "/workouts/{workout_id}",
    response_model=HealthWorkoutResponse,
    dependencies=[Depends(require_editor)],
)
async def link_workout(
    workout_id: Annotated[str, uuid.UUID], request: LinkHealthWorkoutRequest
) -> DBHealthWorkout:
    """Links a workout to a session by hand, or unlinks it with null.
    Automatic matching leaves it alone from then on."""
    try:
        workout = health.link_workout(_workout_uuid(workout_id), request.session_id)
    except SessionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SessionAlreadyLinked as e:
        raise HTTPException(
            status_code=409,
            detail={"detail": str(e), "workout_id": str(e.workout_id)},
        )
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@router.get(
    "/days",
    response_model=List[HealthDayResponse],
    dependencies=[Depends(require_viewer)],
)
async def get_days(
    request: Annotated[ListHealthDaysRequest, Query()],
) -> List[DBHealthDay]:
    """Lists days oldest first."""
    return health.get_days(request=request)


@router.put(
    "/days/{date}",
    response_model=HealthDayResponse,
    dependencies=[Depends(require_editor)],
)
async def put_day(date: datetime.date, request: PutHealthDayRequest) -> DBHealthDay:
    """Creates or replaces one day's sleep and measurements. For sleep, the
    date is the one it was woken up on."""
    return health.put_day(date, request)
