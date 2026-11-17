import uuid
from typing import List, Optional, Tuple

from sqlalchemy import exists

from src.config import Config
from src.db import session
from src.models.squash import Game as DBGame
from src.models.squash import Match as DBMatch
from src.models.squash import MatchPlayer as DBMatchPlayer
from src.models.squash import Player as DBPlayer
from src.models.squash import Rally as DBRally
from src.models.squash import Venue as DBVenue
from src.resolvers.squash import scoring
from src.resolvers.squash.players import NotAllowed, NotFound, SquashCaller
from src.schemas.squash.enums import MatchStatus
from src.schemas.squash.matches import (
    GameRequest,
    GameResponse,
    ListMatchesRequest,
    MatchPlayerRequest,
    MatchRequest,
    MatchResponse,
    MergeMatchesRequest,
    RallyRequest,
    RallyResponse,
)


def _scores(match: DBMatch) -> List[Tuple[int, int]]:
    return [(game.side1_points, game.side2_points) for game in match.games]


def _serving_side(match: DBMatch) -> Optional[int]:
    if not match.games:
        return None
    last = match.games[-1]
    won = [rally for rally in last.rallies if rally.won_by_side is not None]
    if last.rallies and not won:
        # Only lets so far, so whoever served the first one serves again
        return _side_of(match, last.rallies[-1].server_id) or (
            scoring.serving_side(
                (match.games[-2].side1_points, match.games[-2].side2_points),
                None,
                match.points_to,
            )
            if len(match.games) > 1
            else None
        )
    return scoring.serving_side(
        (last.side1_points, last.side2_points),
        won[-1].won_by_side if won else None,
        match.points_to,
    )


def _side_of(match: DBMatch, player_id: Optional[uuid.UUID]) -> Optional[int]:
    return next(
        (player.side for player in match.players if player.player_id == player_id),
        None,
    )


def to_response(match: DBMatch) -> MatchResponse:
    scores = _scores(match)
    side1_games, side2_games = scoring.games_won(scores, match.points_to)
    return MatchResponse(
        id=match.id,
        format=match.format,
        status=match.status,
        played_at=match.played_at,
        venue_id=match.venue_id,
        venue=match.venue.name if match.venue else None,
        points_to=match.points_to,
        best_of=match.best_of,
        notes=match.notes,
        players=[MatchPlayerRequest.model_validate(player) for player in match.players],
        games=[
            GameResponse(
                number=game.number,
                side1_points=game.side1_points,
                side2_points=game.side2_points,
                winning_side=scoring.game_winner(
                    game.side1_points, game.side2_points, match.points_to
                ),
                rallies=len(game.rallies),
            )
            for game in match.games
        ],
        side1_games=side1_games,
        side2_games=side2_games,
        winning_side=match.winning_side,
        serving_side=_serving_side(match),
        version=match.version,
        created_by_id=match.created_by_id,
        created_at=match.created_at,
        updated_at=match.updated_at,
    )


def _check_can_change(match: DBMatch, caller: SquashCaller) -> None:
    """A match can be changed by whoever arranged it, anyone playing in it, or
    an admin."""
    if caller.is_admin or match.created_by_id == caller.user.id:
        return
    if caller.player and any(
        player.player_id == caller.player.id for player in match.players
    ):
        return
    raise NotAllowed("Only the match's players or whoever arranged it can change it")


def _check_players(players: List[MatchPlayerRequest]) -> None:
    for player in players:
        if session.get(DBPlayer, player.player_id) is None:
            raise NotFound(f"Player {player.player_id} not found")


class StaleVersion(ValueError):
    """Raised when a change was made against an older version of a match,
    such as two people scoring the same rally."""

    def __init__(self, match: DBMatch, version: int) -> None:
        self.match = match
        super().__init__(
            f"The match has changed since version {version}, it's now at "
            f"version {match.version}"
        )


def _check_version(match: DBMatch, version: int) -> None:
    if match.version != version:
        raise StaleVersion(match, version)


def _settle(match: DBMatch, scored: bool = False) -> None:
    """Checks the games fit the match's rules, keeps its status and result in
    step with them, and moves it on a version, since every change ends here.

    When it's the score that changed, a best-of match completes itself on
    the point that decides it, and reopens if that point is undone.
    Otherwise the status is what was asked for, and completing a match is
    rejected unless final_result allows it.
    """
    match.version = (match.version or 0) + 1
    scores = _scores(match)
    scoring.check_match_games(scores, match.points_to, match.best_of)
    winner = scoring.match_winner(scores, match.points_to, match.best_of)

    if scored and match.best_of is not None:
        if winner is not None and match.status != MatchStatus.CANCELLED.value:
            match.status = MatchStatus.COMPLETED.value
        elif winner is None and match.status == MatchStatus.COMPLETED.value:
            match.status = MatchStatus.IN_PROGRESS.value

    if match.status == MatchStatus.COMPLETED.value:
        # None for a draw
        match.winning_side = scoring.final_result(
            scores, match.points_to, match.best_of
        )
        return
    match.winning_side = None
    # Scoring a game starts a match that was only arranged
    if scores and match.status == MatchStatus.SCHEDULED.value:
        match.status = MatchStatus.IN_PROGRESS.value


def get_matches(request: ListMatchesRequest) -> List[DBMatch]:
    """Lists matches, most recently played first, then those not yet dated."""
    conditions = []
    if request.player_id:
        conditions.append(
            exists().where(
                DBMatchPlayer.match_id == DBMatch.id,
                DBMatchPlayer.player_id == request.player_id,
            )
        )
    if request.status:
        conditions.append(DBMatch.status == request.status.value)
    if request.format:
        conditions.append(DBMatch.format == request.format.value)
    if request.venue_id:
        conditions.append(DBMatch.venue_id == request.venue_id)
    if request.after:
        conditions.append(DBMatch.played_at >= request.after)
    if request.before:
        conditions.append(DBMatch.played_at <= request.before)

    return (
        session.query(DBMatch)
        .filter(*conditions)
        .order_by(
            DBMatch.played_at.desc().nulls_last(),
            DBMatch.created_at.desc(),
            DBMatch.id,
        )
        .limit(Config.DEFAULT_DB_PAGE_SIZE)
        .offset(request.offset)
        .all()
    )


def get_match(match_id: uuid.UUID) -> Optional[DBMatch]:
    return session.get(DBMatch, match_id)


def _apply(match: DBMatch, request: MatchRequest) -> None:
    _check_players(request.players)
    venue = None
    if request.venue_id:
        venue = session.get(DBVenue, request.venue_id)
        if venue is None:
            raise NotFound(f"Venue {request.venue_id} not found")
    # Set through the relationship, so the response's venue name is current
    match.venue = venue
    fields = request.model_dump(exclude={"players", "venue_id"})
    fields["format"] = request.format.value
    fields["status"] = request.status.value
    for field, value in fields.items():
        setattr(match, field, value)
    match.players = [
        DBMatchPlayer(player_id=player.player_id, side=player.side)
        for player in request.players
    ]
    _settle(match)


def create_match(request: MatchRequest, caller: SquashCaller) -> DBMatch:
    match = DBMatch(id=uuid.uuid4(), created_by_id=caller.user.id, games=[])
    # Only added once it's valid, so a rejected one leaves nothing behind
    _apply(match, request)
    session.add(match)
    session.commit()
    return match


def update_match(
    match_id: uuid.UUID, request: MatchRequest, caller: SquashCaller
) -> Optional[DBMatch]:
    """Replaces every field and the players, keeping the games, which are
    checked again under the new rules."""
    match = get_match(match_id)
    if not match:
        return None
    _check_can_change(match, caller)
    try:
        _apply(match, request)
    except Exception:
        session.rollback()
        raise
    session.commit()
    return match


def complete_match(
    match_id: uuid.UUID, version: int, caller: SquashCaller
) -> Optional[DBMatch]:
    """Ends a match where it stands, for when games are just played until
    people stop. The side with more games wins, or it's a draw."""
    match = get_match(match_id)
    if not match:
        return None
    _check_can_change(match, caller)
    _check_version(match, version)
    if match.status in (MatchStatus.COMPLETED.value, MatchStatus.CANCELLED.value):
        raise scoring.InvalidScore(f"The match is already {match.status}")

    try:
        match.status = MatchStatus.COMPLETED.value
        _settle(match)
    except Exception:
        session.rollback()
        raise
    session.commit()
    return match


def delete_match(match_id: uuid.UUID, caller: SquashCaller) -> bool:
    match = get_match(match_id)
    if not match:
        return False
    _check_can_change(match, caller)
    session.delete(match)
    session.commit()
    return True


def sides_swapped(match: DBMatch, other: DBMatch) -> bool:
    """Whether the same players were on the opposite sides of other, such as
    after swapping ends. Raises when they aren't the same players and pairs."""
    sides = {player.player_id: player.side for player in match.players}
    other_sides = {player.player_id: player.side for player in other.players}
    if match.format != other.format or sides.keys() != other_sides.keys():
        raise scoring.InvalidScore("Only matches between the same players can merge")
    if sides == other_sides:
        return False
    if all(other_sides[player] == 3 - side for player, side in sides.items()):
        return True
    raise scoring.InvalidScore("The players were paired differently in each match")


def played_order(match: DBMatch) -> tuple:
    # Undated matches count as played last
    return (match.played_at is None, match.played_at, match.created_at)


def merged_status(first: DBMatch, second: DBMatch) -> str:
    if first.status == second.status == MatchStatus.COMPLETED.value:
        return MatchStatus.COMPLETED.value
    if first.games or second.games:
        return MatchStatus.IN_PROGRESS.value
    return MatchStatus.SCHEDULED.value


def merge_matches(
    match_id: uuid.UUID, request: MergeMatchesRequest, caller: SquashCaller
) -> Optional[DBMatch]:
    """Folds two matches between the same players into one, such as a
    session recorded as 2 games and then 1 more.

    The match played first is kept, with the other's games after its own,
    and the other is deleted. The merged match has no best_of, since its
    games no longer need to fit one, and is completed only if both were.
    """
    match = get_match(match_id)
    if not match:
        return None
    other = get_match(request.match_id)
    if not other:
        raise NotFound(f"Match {request.match_id} not found")
    if match.id == other.id:
        raise scoring.InvalidScore("A match can't merge with itself")
    _check_can_change(match, caller)
    _check_can_change(other, caller)
    if MatchStatus.CANCELLED.value in (match.status, other.status):
        raise scoring.InvalidScore("A cancelled match can't merge")
    if match.points_to != other.points_to:
        raise scoring.InvalidScore(
            "Only matches with games to the same points can merge"
        )
    first, second = sorted((match, other), key=played_order)
    swapped = sides_swapped(first, second)
    if (
        first.games
        and second.games
        and not scoring.game_winner(
            first.games[-1].side1_points, first.games[-1].side2_points, first.points_to
        )
    ):
        raise scoring.InvalidScore(
            "The earlier match's last game is unfinished, so finish or delete it first"
        )

    try:
        status = merged_status(first, second)
        offset = len(first.games)
        # Otherwise loading a game's rallies would flush it while it's out of
        # both matches, deleting it as an orphan
        with session.no_autoflush:
            moved = list(second.games)
            second.games.clear()
            for game in moved:
                game.number += offset
                if swapped:
                    game.side1_points, game.side2_points = (
                        game.side2_points,
                        game.side1_points,
                    )
                    for rally in game.rallies:
                        if rally.won_by_side:
                            rally.won_by_side = 3 - rally.won_by_side
                        if rally.appealed_by_side:
                            rally.appealed_by_side = 3 - rally.appealed_by_side
                first.games.append(game)

        first.status = status
        first.best_of = None
        first.venue = first.venue or second.venue
        if second.notes and second.notes != first.notes:
            first.notes = "\n".join(filter(None, (first.notes, second.notes)))
        session.delete(second)
        _settle(first)
    except Exception:
        session.rollback()
        raise
    session.commit()
    return first


def set_game(
    match_id: uuid.UUID, number: int, game: GameRequest, caller: SquashCaller
) -> Optional[DBMatch]:
    """Sets a game's score, adding it when it's the next one.

    For entering a game's score after the fact, or correcting one. Setting
    the score of a game scored rally by rally drops its rallies, since they
    would no longer add up to it, and it's then kept as an entered score.
    """
    match = get_match(match_id)
    if not match:
        return None
    _check_can_change(match, caller)
    if not 1 <= number <= len(match.games) + 1:
        raise scoring.InvalidScore(
            f"The next game is game {len(match.games) + 1}, so game {number} "
            "can't be scored"
        )

    try:
        if number > len(match.games):
            match.games.append(
                DBGame(id=uuid.uuid4(), number=number, **game.model_dump())
            )
        else:
            existing = match.games[number - 1]
            existing.rallies.clear()
            existing.side1_points = game.side1_points
            existing.side2_points = game.side2_points
        _settle(match, scored=True)
    except Exception:
        session.rollback()
        raise
    session.commit()
    return match


def delete_last_game(match_id: uuid.UUID, caller: SquashCaller) -> Optional[DBMatch]:
    """Removes the latest game, such as one added by mistake."""
    match = get_match(match_id)
    if not match:
        return None
    _check_can_change(match, caller)
    if not match.games:
        raise NotFound("The match has no games")
    try:
        match.games.pop()
        _settle(match, scored=True)
    except Exception:
        session.rollback()
        raise
    session.commit()
    return match


def _check_server(match: DBMatch, server_id: Optional[uuid.UUID]) -> None:
    if server_id is None:
        return
    side = _side_of(match, server_id)
    if side is None:
        raise scoring.InvalidScore(f"Player {server_id} isn't playing in this match")
    serving = _serving_side(match)
    if serving is not None and side != serving:
        raise scoring.InvalidScore(f"It's side {serving}'s serve")


def add_rally(
    match_id: uuid.UUID, rally: RallyRequest, caller: SquashCaller
) -> Optional[DBMatch]:
    """Records who won a rally, adding a point to the game in play, or
    starting the next game when the last one's finished. A let adds no
    point, but is kept as a record of the call.

    Only taken against the match's current version, so when two phones score
    the same rally the second is turned away rather than adding a point.
    Requests are handled one at a time (see db_lock), so nothing can change
    between the check and the write.
    """
    match = get_match(match_id)
    if not match:
        return None
    _check_can_change(match, caller)
    _check_version(match, rally.version)
    if match.status in (MatchStatus.COMPLETED.value, MatchStatus.CANCELLED.value):
        raise scoring.InvalidScore(f"The match is {match.status}")
    _check_server(match, rally.server_id)

    try:
        game = match.games[-1] if match.games else None
        if game is None or scoring.game_winner(
            game.side1_points, game.side2_points, match.points_to
        ):
            game = DBGame(
                id=uuid.uuid4(),
                number=len(match.games) + 1,
                side1_points=0,
                side2_points=0,
            )
            match.games.append(game)
        elif not game.rallies and (game.side1_points or game.side2_points):
            raise scoring.InvalidScore(
                f"Game {game.number}'s score was set directly, so it can't be "
                "carried on rally by rally"
            )

        game.rallies.append(
            DBRally(
                id=uuid.uuid4(),
                number=len(game.rallies) + 1,
                won_by_side=rally.won_by_side,
                decision=rally.decision.value if rally.decision else None,
                appealed_by_side=rally.appealing_side,
                server_id=rally.server_id,
            )
        )
        if rally.won_by_side == 1:
            game.side1_points += 1
        elif rally.won_by_side == 2:
            game.side2_points += 1
        _settle(match, scored=True)
    except Exception:
        session.rollback()
        raise
    session.commit()
    return match


def undo_rally(
    match_id: uuid.UUID, version: int, caller: SquashCaller
) -> Optional[DBMatch]:
    """Takes back the latest rally, and the game it started if it was the
    first. Undoing the point that won a best-of match reopens it. Like
    scoring, only against the current version, so two undos take back one
    point."""
    match = get_match(match_id)
    if not match:
        return None
    _check_can_change(match, caller)
    _check_version(match, version)
    game = match.games[-1] if match.games else None
    if game is None or not game.rallies:
        raise NotFound("The match's last game has no rallies to undo")

    try:
        rally = game.rallies.pop()
        if rally.won_by_side == 1:
            game.side1_points -= 1
        elif rally.won_by_side == 2:
            game.side2_points -= 1
        if not game.rallies:
            match.games.pop()
        _settle(match, scored=True)
    except Exception:
        session.rollback()
        raise
    session.commit()
    return match


def get_rallies(match: DBMatch) -> List[RallyResponse]:
    """Every rally of the match in order, with the score after each."""
    rallies = []
    for game in match.games:
        points = {1: 0, 2: 0}
        for rally in game.rallies:
            if rally.won_by_side is not None:
                points[rally.won_by_side] += 1
            rallies.append(
                RallyResponse(
                    game=game.number,
                    number=rally.number,
                    won_by_side=rally.won_by_side,
                    decision=rally.decision,
                    appealed_by_side=rally.appealed_by_side,
                    server_id=rally.server_id,
                    side1_points=points[1],
                    side2_points=points[2],
                    created_at=rally.created_at,
                )
            )
    return rallies
