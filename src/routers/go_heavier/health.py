import datetime
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query

from src.models.go_heavier import HealthDay as DBHealthDay
from src.models.go_heavier import HealthWorkout as DBHealthWorkout
from src.models.user import User
from src.resolvers.go_heavier import health
from src.resolvers.go_heavier.health import (
    SessionAlreadyLinked,
    SessionNotFound,
    SyncedByAnotherUser,
)
from src.resolvers.users import require_admin, require_editor, require_viewer
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

# Admin-only for now, set once here so that a new route can't be added
# without it. The per-route viewer/editor gates are kept underneath, so
# opening it up again is just removing this.
router = APIRouter(
    prefix="/go-heavier/health",
    tags=["health"],
    dependencies=[Depends(require_admin)],
)


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


@router.put("/workouts/{workout_id}", response_model=HealthWorkoutResponse)
async def put_workout(
    workout_id: Annotated[str, uuid.UUID],
    request: PutHealthWorkoutRequest,
    user: Annotated[User, Depends(require_editor)],
) -> DBHealthWorkout:
    """Creates or replaces a workout, keyed by its HealthKit UUID, so it can
    be sent any number of times. Unless it was linked by hand, it's linked to
    the session it was recorded during: the one whose workout_time falls
    between two hours before the workout started and when it ended, nearest
    the start, that no other workout has. Workouts under five minutes aren't
    matched. It's associated with the caller if it isn't already; 403 if
    another user synced it."""
    try:
        return health.put_workout(_workout_uuid(workout_id), request, user)
    except SyncedByAnotherUser as e:
        raise HTTPException(status_code=403, detail=str(e))


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


@router.put("/days/{date}", response_model=HealthDayResponse)
async def put_day(
    date: datetime.date,
    request: PutHealthDayRequest,
    user: Annotated[User, Depends(require_editor)],
) -> DBHealthDay:
    """Creates or replaces one day's sleep and measurements. For sleep, the
    date is the one it was woken up on. It's associated with the caller if
    it isn't already; 403 if another user synced it."""
    try:
        return health.put_day(date, request, user)
    except SyncedByAnotherUser as e:
        raise HTTPException(status_code=403, detail=str(e))
