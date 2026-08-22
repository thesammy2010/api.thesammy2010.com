import uuid
from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Query

from src.resolvers.go_heavier import sessions
from src.schemas.go_heavier.session_stats import (
    SessionStatsRequest,
    SessionStatsResponse,
)
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


@router.get("/sessions/stats", response_model=SessionStatsResponse)
async def get_session_stats(
    request: Annotated[SessionStatsRequest, Query()],
) -> SessionStatsResponse:
    return sessions.get_session_stats(request=request)


# Declared after /sessions/stats so that "stats" is not read as a session id
@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: Annotated[str, uuid.UUID]) -> SessionResponse:
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for session id"},
        )
    workout_session = sessions.get_session(session_id=session_uuid)
    if not workout_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return workout_session
