import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query

from src.resolvers.squash import matches, players, reports
from src.resolvers.squash.players import require_squash_player
from src.routers.squash import parse_uuid
from src.schemas.squash.insights import (
    MatchInsightsResponse,
    PlayerInsightsResponse,
    RatingChangeResponse,
    RatingFormatRequest,
    RatingResponse,
    RatingsRequest,
)

router = APIRouter(
    prefix="/squash",
    tags=["squash ratings and insights"],
    dependencies=[Depends(require_squash_player)],
)


def _player_id(player_id: str) -> uuid.UUID:
    player = players.get_player(parse_uuid(player_id, "player"))
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player.id


@router.get("/ratings", response_model=List[RatingResponse])
def get_ratings(
    request: Annotated[RatingsRequest, Query()],
) -> List[RatingResponse]:
    """The Elo ladder, highest rated first. Everyone starts on 1000, and each
    completed match moves the winners up and the losers down by the same
    amount, more for beating someone rated higher. A draw moves the
    higher rated side down a little. In doubles a pair plays as the average
    of the two. Worked out afresh from every completed match, so correcting
    or deleting one updates every rating after it."""
    return reports.get_ratings(request)


@router.get("/players/{player_id}/ratings", response_model=List[RatingChangeResponse])
def get_rating_history(
    player_id: Annotated[str, uuid.UUID],
    request: Annotated[RatingFormatRequest, Query()],
) -> List[RatingChangeResponse]:
    """What each of a player's completed matches did to their rating, oldest
    first, such as for a chart. Empty before they've played one."""
    return reports.get_rating_history(_player_id(player_id), request.format)


@router.get("/players/{player_id}/insights", response_model=PlayerInsightsResponse)
def get_player_insights(
    player_id: Annotated[str, uuid.UUID],
    request: Annotated[RatingFormatRequest, Query()],
) -> PlayerInsightsResponse:
    """How a player's completed matches went point by point: rallies won on
    and against serve, runs of points, game points taken, comebacks and
    leads lost. Only games scored live have rallies to count, apart from
    deuce games, which any final score shows."""
    return reports.get_player_insights(_player_id(player_id), request.format)


@router.get("/matches/{match_id}/insights", response_model=MatchInsightsResponse)
def get_match_insights(match_id: Annotated[str, uuid.UUID]) -> MatchInsightsResponse:
    """A match point by point, each side and each game: rallies won on and
    against serve, runs, leads, game points and comebacks. Works while it's
    being played too."""
    match = matches.get_match(parse_uuid(match_id, "match"))
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return reports.get_match_insights(match)
