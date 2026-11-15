import uuid
from typing import Annotated, Callable, List, Optional, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from fastapi.encoders import jsonable_encoder

from src.resolvers.squash import matches
from src.resolvers.squash.matches import StaleVersion
from src.resolvers.squash.players import (
    NotAllowed,
    NotFound,
    SquashCaller,
    require_squash_player,
)
from src.resolvers.squash.scoring import InvalidScore
from src.routers.squash import parse_uuid
from src.schemas.squash.matches import (
    GameRequest,
    ListMatchesRequest,
    MatchRequest,
    MatchResponse,
    RallyRequest,
    RallyResponse,
)

router = APIRouter(
    prefix="/squash",
    tags=["squash matches"],
    dependencies=[Depends(require_squash_player)],
)

Caller = Annotated[SquashCaller, Depends(require_squash_player)]
T = TypeVar("T")


def _handle(call: Callable[[], T]) -> T:
    """Turns the resolvers' errors into their HTTP statuses."""
    try:
        return call()
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotAllowed as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InvalidScore as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StaleVersion as e:
        # With the match as it is now, so the phone can show it straight away
        raise HTTPException(
            status_code=409,
            detail={
                "detail": str(e),
                "match": jsonable_encoder(matches.to_response(e.match)),
            },
        )


def _found(match) -> MatchResponse:
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return matches.to_response(match)


@router.get("/matches", response_model=List[MatchResponse])
def get_matches(
    request: Annotated[ListMatchesRequest, Query()],
) -> List[MatchResponse]:
    """Lists matches, most recently played first, then any not yet dated."""
    return [matches.to_response(match) for match in matches.get_matches(request)]


@router.get(
    "/matches/{match_id}",
    response_model=MatchResponse,
    responses={204: {"description": "The match is still at since_version"}},
)
def get_match(
    match_id: Annotated[str, uuid.UUID],
    since_version: Annotated[
        Optional[int],
        Query(
            description="The version already shown. 204 with no body until "
            "the match moves past it, so polling during a match is cheap"
        ),
    ] = None,
):
    """A match with its games. To follow one live, poll this every second or
    two with `since_version`."""
    match = matches.get_match(parse_uuid(match_id, "match"))
    if match and since_version is not None and match.version == since_version:
        return Response(status_code=204)
    return _found(match)


@router.post("/matches", response_model=MatchResponse)
def create_match(request: MatchRequest, caller: Caller) -> MatchResponse:
    """Arranges a match, or records one already played. Any player can,
    including for a match they aren't in. 404 if a player doesn't exist."""
    return _found(_handle(lambda: matches.create_match(request, caller)))


@router.put("/matches/{match_id}", response_model=MatchResponse)
def update_match(
    match_id: Annotated[str, uuid.UUID], request: MatchRequest, caller: Caller
) -> MatchResponse:
    """Replaces a match's fields and players, keeping its games. Set
    `status` to `completed` once the games decide it, which is 400 until
    they do. 403 unless the caller plays in it, arranged it, or is an
    admin."""
    match_uuid = parse_uuid(match_id, "match")
    return _found(_handle(lambda: matches.update_match(match_uuid, request, caller)))


@router.post("/matches/{match_id}/complete", response_model=MatchResponse)
def complete_match(
    match_id: Annotated[str, uuid.UUID],
    version: Annotated[
        int, Query(description="The match's version being completed from")
    ],
    caller: Caller,
) -> MatchResponse:
    """Ends a match where it stands, for when games are just played until
    people stop. The side that won more games wins, and level games are a
    draw, with `winning_side` null. A game left unfinished doesn't count. A
    best-of match completes itself on its deciding point, so this is only
    needed for one once that's been won, such as after setting its games
    by hand. 400 before any game is finished, for a best-of match not yet
    won, or one already completed or cancelled. 409 if `version` isn't
    current."""
    match_uuid = parse_uuid(match_id, "match")
    return _found(_handle(lambda: matches.complete_match(match_uuid, version, caller)))


@router.delete("/matches/{match_id}", status_code=204)
def delete_match(match_id: Annotated[str, uuid.UUID], caller: Caller) -> Response:
    """Deletes a match and its games."""
    match_uuid = parse_uuid(match_id, "match")
    if not _handle(lambda: matches.delete_match(match_uuid, caller)):
        raise HTTPException(status_code=404, detail="Match not found")
    return Response(status_code=204)


@router.put("/matches/{match_id}/games/{number}", response_model=MatchResponse)
def set_game(
    match_id: Annotated[str, uuid.UUID],
    number: Annotated[int, Path(ge=1)],
    game: GameRequest,
    caller: Caller,
) -> MatchResponse:
    """Sets a game's score, adding it if it's the next game, for entering
    scores after the fact. To score live, post rallies instead. Scoring the
    first game starts a scheduled match, and the game that decides a
    best-of match completes it. 400 for a score that couldn't happen, such
    as 12-5 in a game to 11, a game after the match was won, or a change to
    a game scored rally by rally."""
    match_uuid = parse_uuid(match_id, "match")
    return _found(_handle(lambda: matches.set_game(match_uuid, number, game, caller)))


@router.delete("/matches/{match_id}/games/last", response_model=MatchResponse)
def delete_last_game(
    match_id: Annotated[str, uuid.UUID], caller: Caller
) -> MatchResponse:
    """Removes the latest game, such as one added by mistake."""
    match_uuid = parse_uuid(match_id, "match")
    return _found(_handle(lambda: matches.delete_last_game(match_uuid, caller)))


@router.get("/matches/{match_id}/rallies", response_model=List[RallyResponse])
def get_rallies(match_id: Annotated[str, uuid.UUID]) -> List[RallyResponse]:
    """Every rally of the match in order, with the score after each."""
    match = matches.get_match(parse_uuid(match_id, "match"))
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return matches.get_rallies(match)


@router.post("/matches/{match_id}/rallies", response_model=MatchResponse)
def add_rally(
    match_id: Annotated[str, uuid.UUID], rally: RallyRequest, caller: Caller
) -> MatchResponse:
    """Scores a match live: records who won a rally, adding the point to the
    game in play or starting the next one. The response's `serving_side`
    says who serves next. The point that decides a best-of match completes
    it. 409, with the match as it is now, if `version` isn't current, such
    as when someone else scored the rally first. 400 once the match is
    completed or cancelled, or if `server_id` isn't on the side whose serve
    it was."""
    match_uuid = parse_uuid(match_id, "match")
    return _found(_handle(lambda: matches.add_rally(match_uuid, rally, caller)))


@router.delete("/matches/{match_id}/rallies/last", response_model=MatchResponse)
def undo_rally(
    match_id: Annotated[str, uuid.UUID],
    version: Annotated[int, Query(description="The match's version being undone from")],
    caller: Caller,
) -> MatchResponse:
    """Undoes the latest rally, such as a point given to the wrong side. Undoing
    the point that won a best-of match reopens it. 409, with the match as it
    is now, if `version` isn't current, so two people undoing at once take
    back one point."""
    match_uuid = parse_uuid(match_id, "match")
    return _found(_handle(lambda: matches.undo_rally(match_uuid, version, caller)))
