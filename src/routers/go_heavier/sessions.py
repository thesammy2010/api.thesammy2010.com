import datetime
from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Query

from src.resolvers.go_heavier import sessions
from src.schemas.go_heavier.sessions import (
    ListSessionsRequest,
    SessionResponse,
    SessionSummary,
)

router = APIRouter(prefix="/go-heavier", tags=["sessions"])


@router.get("/sessions", response_model=List[SessionSummary])
async def get_sessions(
    request: Annotated[ListSessionsRequest, Query()],
) -> List[SessionSummary]:
    return sessions.get_sessions(request=request)


@router.get("/sessions/{workout_time}", response_model=SessionResponse)
async def get_session(workout_time: str) -> SessionResponse:
    try:
        parsed = datetime.datetime.fromisoformat(workout_time)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for workout time, expected ISO 8601"},
        )
    # A session key read off a listing is in UTC, and a bare one is taken as UTC
    # rather than as the server's local time.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)

    workout_session = sessions.get_session(workout_time=parsed)
    if not workout_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return workout_session
