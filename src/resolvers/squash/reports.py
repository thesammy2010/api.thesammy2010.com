"""Ratings and point-by-point insights, worked out from the matches.

Like stats, counted in Python on every request: the group plays a few
matches a week, so there's little to load.
"""

import uuid
from typing import List, Optional

from sqlalchemy import exists

from src.db import session
from src.models.squash import Match as DBMatch
from src.models.squash import MatchPlayer as DBMatchPlayer
from src.models.squash import Player as DBPlayer
from src.resolvers.squash import elo, insights, scoring
from src.resolvers.squash.matches import visible_to
from src.resolvers.squash.players import SquashCaller
from src.schemas.squash.enums import MatchFormat, MatchStatus
from src.schemas.squash.insights import (
    GameInsightsResponse,
    MatchInsightsResponse,
    PlayerInsightsResponse,
    RallyInsightsResponse,
    RatingChangeResponse,
    RatingResponse,
    RatingsRequest,
)


def _completed(
    format: Optional[MatchFormat],
    player_id: Optional[uuid.UUID] = None,
    caller: Optional[SquashCaller] = None,
) -> List[DBMatch]:
    """Completed matches in the order played, undated ones last. Private
    ones are left out unless the caller can see them, and always without a
    caller, since ratings are shared and would give a result away."""
    conditions = [DBMatch.status == MatchStatus.COMPLETED.value]
    conditions.append(visible_to(caller) if caller else DBMatch.is_private.is_(False))
    if format:
        conditions.append(DBMatch.format == format.value)
    if player_id:
        conditions.append(
            exists().where(
                DBMatchPlayer.match_id == DBMatch.id,
                DBMatchPlayer.player_id == player_id,
            )
        )
    return (
        session.query(DBMatch)
        .filter(*conditions)
        .order_by(DBMatch.played_at.asc().nulls_last(), DBMatch.created_at, DBMatch.id)
        .all()
    )


def get_ratings(request: RatingsRequest) -> List[RatingResponse]:
    """The ladder, highest rated first, of players who've played a match."""
    ratings = elo.rate(_completed(request.format))
    players = session.query(DBPlayer).filter(DBPlayer.id.in_(ratings.keys())).all()
    if not request.include_inactive:
        players = [player for player in players if player.is_active]
    players.sort(key=lambda player: (-ratings[player.id].rating, player.name))

    ladder = []
    for rank, player in enumerate(players, start=1):
        rating = ratings[player.id]
        last = rating.history[-1]
        ladder.append(
            RatingResponse(
                rank=rank,
                player_id=player.id,
                name=player.name,
                rating=round(rating.rating),
                matches_rated=rating.matches,
                provisional=rating.matches < elo.PROVISIONAL_MATCHES,
                peak=round(rating.peak),
                last_change=round(last.after) - round(last.before),
            )
        )
    return ladder


def get_rating_history(
    player_id: uuid.UUID, format: Optional[MatchFormat]
) -> List[RatingChangeResponse]:
    """What each of a player's matches did to their rating, oldest first.

    Everyone's matches are replayed, since a player's rating moves on who
    their opponents had become by then.
    """
    rating = elo.rate(_completed(format)).get(player_id)
    if rating is None:
        return []
    return [
        RatingChangeResponse(
            match_id=change.match_id,
            played_at=change.played_at,
            rating_before=round(change.before),
            rating_after=round(change.after),
            change=round(change.after) - round(change.before),
        )
        for change in rating.history
    ]


def get_player_insights(
    player_id: uuid.UUID, format: Optional[MatchFormat], caller: SquashCaller
) -> PlayerInsightsResponse:
    found = insights.player_insights(_completed(format, player_id, caller), player_id)
    return PlayerInsightsResponse(
        player_id=player_id,
        games_scored_live=found.games_scored_live,
        rallies=RallyInsightsResponse.from_tally(found.tally),
        comebacks=found.comebacks,
        biggest_comeback=found.biggest_comeback,
        leads_lost=found.leads_lost,
        deuce_games_won=found.deuce_games_won,
        deuce_games_lost=found.deuce_games_lost,
    )


def get_match_insights(match: DBMatch) -> MatchInsightsResponse:
    totals = {side: insights.Tally() for side in scoring.SIDES}
    games = []
    for game, replay in zip(match.games, insights.replay_match(match)):
        winner = scoring.game_winner(
            game.side1_points, game.side2_points, match.points_to
        )
        deficit = replay.deepest_deficit[winner] if replay and winner else None
        if replay:
            for side in scoring.SIDES:
                totals[side].add(replay.tallies[side])
        games.append(
            GameInsightsResponse(
                number=game.number,
                scored_live=replay is not None,
                lets=replay.lets if replay else 0,
                went_to_deuce=insights.went_to_deuce(
                    game.side1_points, game.side2_points, match.points_to
                ),
                comeback_by_side=(
                    winner
                    if deficit is not None and deficit >= insights.COMEBACK_DEFICIT
                    else None
                ),
                deepest_deficit=deficit,
                sides=(
                    [
                        RallyInsightsResponse.from_tally(replay.tallies[side], side)
                        for side in scoring.SIDES
                    ]
                    if replay
                    else []
                ),
            )
        )
    return MatchInsightsResponse(
        match_id=match.id,
        sides=[
            RallyInsightsResponse.from_tally(totals[side], side)
            for side in scoring.SIDES
        ],
        games=games,
    )
