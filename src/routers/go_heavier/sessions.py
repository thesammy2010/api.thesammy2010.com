import logging
import uuid
from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Query, Response

from src.resolvers.go_heavier import sessions
from src.resolvers.go_heavier.sessions import (
    LocationNotFound,
    SessionAlreadyExists,
)
from src.schemas.go_heavier.session_stats import (
    SessionStatsRequest,
    SessionStatsResponse,
)
from src.schemas.go_heavier.sessions import (
    CreateSessionRequest,
    ListSessionsRequest,
    SessionResponse,
    SessionSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/go-heavier", tags=["sessions"])


@router.get("/sessions", response_model=List[SessionSummary])
async def get_sessions(
    request: Annotated[ListSessionsRequest, Query()],
) -> List[SessionSummary]:
    return sessions.get_sessions(request=request)


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(request: CreateSessionRequest) -> SessionResponse:
    try:
        return sessions.create_session(request=request)
    except LocationNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SessionAlreadyExists as e:
        raise HTTPException(
            status_code=409,
            detail={"detail": str(e), "session_id": str(e.session_id)},
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


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


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: Annotated[str, uuid.UUID]) -> Response:
    """Delete a session and every set logged against it."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for session id"},
        )
    if not sessions.delete_session(session_id=session_uuid):
        raise HTTPException(status_code=404, detail="Session not found")
    return Response(status_code=204)
