"""Players' records, worked out from their completed matches.

Counted in Python rather than SQL: the group plays a few matches a week, so
there's little to load, and the game-by-game rules live in scoring.
"""

import uuid
from typing import Iterable, List, Optional

from sqlalchemy import exists

from src.db import session
from src.models.squash import Match as DBMatch
from src.models.squash import MatchPlayer as DBMatchPlayer
from src.resolvers.squash import scoring
from src.schemas.squash.enums import MatchFormat, MatchStatus
from src.schemas.squash.players import (
    HeadToHeadResponse,
    PlayerRecord,
    PlayerStatsResponse,
)


def _completed_with(*player_ids: uuid.UUID) -> List[DBMatch]:
    return (
        session.query(DBMatch)
        .filter(
            DBMatch.status == MatchStatus.COMPLETED.value,
            *[
                exists().where(
                    DBMatchPlayer.match_id == DBMatch.id,
                    DBMatchPlayer.player_id == player_id,
                )
                for player_id in player_ids
            ],
        )
        .all()
    )


def _side(match: DBMatch, player_id: uuid.UUID) -> Optional[int]:
    return next(
        (player.side for player in match.players if player.player_id == player_id),
        None,
    )


def win_rate(won: int, lost: int) -> Optional[float]:
    """The share of matches won out of those won or lost, so a draw counts
    neither for nor against."""
    if not won + lost:
        return None
    return round(won / (won + lost), 3)


def get_player_stats(player_id: uuid.UUID) -> PlayerStatsResponse:
    matches = _completed_with(player_id)
    return PlayerStatsResponse(
        player_id=player_id,
        **record(matches, player_id).model_dump(),
        singles=record(
            (m for m in matches if m.format == MatchFormat.SINGLES.value), player_id
        ),
        doubles=record(
            (m for m in matches if m.format == MatchFormat.DOUBLES.value), player_id
        ),
    )


def record(matches: Iterable[DBMatch], player_id: uuid.UUID) -> PlayerRecord:
    """The player's record across these completed matches, each of which
    they played in."""
    matches = list(matches)
    matches_won = matches_drawn = games_won = games_lost = 0
    points_won = points_lost = 0
    for match in matches:
        side = _side(match, player_id)
        if match.winning_side is None:
            matches_drawn += 1
        elif match.winning_side == side:
            matches_won += 1
        for game in match.games:
            mine, theirs = (
                (game.side1_points, game.side2_points)
                if side == 1
                else (game.side2_points, game.side1_points)
            )
            points_won += mine
            points_lost += theirs
            winner = scoring.game_winner(mine, theirs, match.points_to)
            games_won += winner == 1
            games_lost += winner == 2

    matches_lost = len(matches) - matches_won - matches_drawn
    return PlayerRecord(
        matches_played=len(matches),
        matches_won=matches_won,
        matches_lost=matches_lost,
        matches_drawn=matches_drawn,
        games_won=games_won,
        games_lost=games_lost,
        points_won=points_won,
        points_lost=points_lost,
        win_rate=win_rate(matches_won, matches_lost),
    )


def get_head_to_head(
    player_id: uuid.UUID, opponent_id: uuid.UUID
) -> HeadToHeadResponse:
    """Matches the two played on opposite sides, doubles included."""
    played = won = drawn = games_won = games_lost = 0
    for match in _completed_with(player_id, opponent_id):
        side = _side(match, player_id)
        if side == _side(match, opponent_id):
            continue
        played += 1
        if match.winning_side is None:
            drawn += 1
        elif match.winning_side == side:
            won += 1
        side1_games, side2_games = scoring.games_won(
            [(game.side1_points, game.side2_points) for game in match.games],
            match.points_to,
        )
        mine, theirs = (
            (side1_games, side2_games) if side == 1 else (side2_games, side1_games)
        )
        games_won += mine
        games_lost += theirs

    return HeadToHeadResponse(
        player_id=player_id,
        opponent_id=opponent_id,
        matches_played=played,
        matches_won=won,
        matches_lost=played - won - drawn,
        matches_drawn=drawn,
        games_won=games_won,
        games_lost=games_lost,
    )
