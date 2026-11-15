import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query

from src.models.squash import Player as DBPlayer
from src.resolvers.squash import players, stats
from src.resolvers.squash.players import (
    Conflict,
    NotFound,
    SquashCaller,
    require_squash_admin,
    require_squash_player,
)
from src.routers.squash import parse_uuid
from src.schemas.squash.players import (
    HeadToHeadResponse,
    PlayerRequest,
    PlayerResponse,
    PlayerStatsResponse,
)

# Every squash route is for the group's players, set once here so that a new
# route can't be added without it
router = APIRouter(
    prefix="/squash",
    tags=["squash players"],
    dependencies=[Depends(require_squash_player)],
)


def _player(player_id: str) -> DBPlayer:
    player = players.get_player(parse_uuid(player_id, "player"))
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.get("/players", response_model=List[PlayerResponse])
def get_players(
    include_inactive: Annotated[bool, Query()] = False,
) -> List[DBPlayer]:
    """The players in the group, by name."""
    return players.get_players(include_inactive=include_inactive)


@router.get("/players/me", response_model=PlayerResponse)
def get_me(
    caller: Annotated[SquashCaller, Depends(require_squash_player)],
) -> DBPlayer:
    """The caller's own player. 404 for an admin who isn't one."""
    if caller.player is None:
        raise HTTPException(status_code=404, detail="You aren't a player")
    return caller.player


@router.get("/players/{player_id}", response_model=PlayerResponse)
def get_player(player_id: Annotated[str, uuid.UUID]) -> DBPlayer:
    return _player(player_id)


@router.get("/players/{player_id}/stats", response_model=PlayerStatsResponse)
def get_player_stats(player_id: Annotated[str, uuid.UUID]) -> PlayerStatsResponse:
    """A player's record across their completed matches, doubles included."""
    return stats.get_player_stats(_player(player_id).id)


@router.get(
    "/players/{player_id}/head-to-head/{opponent_id}",
    response_model=HeadToHeadResponse,
)
def get_head_to_head(
    player_id: Annotated[str, uuid.UUID], opponent_id: Annotated[str, uuid.UUID]
) -> HeadToHeadResponse:
    """Two players' completed matches on opposite sides of the court."""
    return stats.get_head_to_head(_player(player_id).id, _player(opponent_id).id)


@router.post(
    "/players",
    response_model=PlayerResponse,
    dependencies=[Depends(require_squash_admin)],
)
def create_player(player: PlayerRequest) -> DBPlayer:
    """Adds someone to the group. Admin-only. Linked to a user, it lets them
    sign in and use /squash. 404 if the user doesn't exist, 409 if they're
    already a player."""
    try:
        return players.create_player(player)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put(
    "/players/{player_id}",
    response_model=PlayerResponse,
    dependencies=[Depends(require_squash_admin)],
)
def update_player(
    player_id: Annotated[str, uuid.UUID], player: PlayerRequest
) -> DBPlayer:
    """Replaces a player's fields, such as to link them to the user they've
    signed in as, or to take them out of the group. Admin-only."""
    try:
        updated = players.update_player(parse_uuid(player_id, "player"), player)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="Player not found")
    return updated
