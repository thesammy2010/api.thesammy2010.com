"""The rules of a squash game and match, under point-a-rally scoring.

Kept free of any database import so that it stays unit testable.
"""

from typing import List, Optional, Tuple

SIDES = (1, 2)


class InvalidScore(ValueError):
    """Raised when a score couldn't have happened under the match's rules."""


def game_winner(side1: int, side2: int, points_to: int) -> Optional[int]:
    """The side that won a game with this score, or None while it's still on.

    A game goes to the first to points_to, except that from points_to - 1
    all it carries on until one side is two clear, so 11-9 and 12-10 are
    finished but 11-10 isn't.
    """
    high, low = max(side1, side2), min(side1, side2)
    if high >= points_to and high - low >= 2:
        return 1 if side1 > side2 else 2
    return None


def check_game_score(side1: int, side2: int, points_to: int) -> None:
    """Rejects a score that play would have stopped before reaching.

    11-5 and 13-11 can be final scores, but 12-5 can't, since the game
    ended at 11-5, nor can 14-11, since it ended at 13-11.
    """
    if side1 < 0 or side2 < 0:
        raise InvalidScore("Points can't be negative")
    high, low = max(side1, side2), min(side1, side2)
    if high <= points_to:
        return
    # Past points_to the game only goes on from deuce, so it ends exactly two
    # clear
    if low < points_to - 1 or high - low > 2:
        raise InvalidScore(
            f"{side1}-{side2} isn't possible in a game to {points_to}: it "
            "would have finished sooner"
        )


def games_won(games: List[Tuple[int, int]], points_to: int) -> Tuple[int, int]:
    """How many finished games each side has won."""
    won = {side: 0 for side in SIDES}
    for side1, side2 in games:
        winner = game_winner(side1, side2, points_to)
        if winner:
            won[winner] += 1
    return won[1], won[2]


def match_winner(
    games: List[Tuple[int, int]], points_to: int, best_of: Optional[int]
) -> Optional[int]:
    """The side that has won the match, or None if it isn't decided.

    Without best_of, the games are just played until people stop, so the
    side that won more of them won, and it's undecided on equal games.
    """
    side1, side2 = games_won(games, points_to)
    if best_of is not None:
        needed = best_of // 2 + 1
        if side1 >= needed:
            return 1
        if side2 >= needed:
            return 2
        return None
    if side1 == side2:
        return None
    return 1 if side1 > side2 else 2


def check_match_games(
    games: List[Tuple[int, int]], points_to: int, best_of: Optional[int]
) -> None:
    """Rejects games that couldn't all have been played in one match.

    Only the last game may be unfinished, and none may follow the one that
    decided a best-of match.
    """
    for number, (side1, side2) in enumerate(games, start=1):
        check_game_score(side1, side2, points_to)
        if number < len(games) and game_winner(side1, side2, points_to) is None:
            raise InvalidScore(f"Game {number} is unfinished but isn't the last")
    if best_of is not None:
        if len(games) > best_of:
            raise InvalidScore(f"A best of {best_of} has at most {best_of} games")
        if games and match_winner(games[:-1], points_to, best_of) is not None:
            raise InvalidScore("The match was already won before the last game")


def serving_side(
    last_game: Optional[Tuple[int, int]],
    last_rally_won_by: Optional[int],
    points_to: int,
) -> Optional[int]:
    """The side to serve next, or None when there's no telling.

    Under point-a-rally the winner of a rally serves the next, and the
    winner of a game serves first in the next game. Before the first rally,
    or in a game scored without its rallies, it's down to a spin of the
    racket.
    """
    if last_game is None:
        return None
    winner = game_winner(*last_game, points_to)
    if winner is not None:
        return winner
    return last_rally_won_by


def final_result(
    games: List[Tuple[int, int]], points_to: int, best_of: Optional[int]
) -> Optional[int]:
    """The side that won a match being completed, or None for a draw.

    A best-of match has to have been won. One where games were just played
    until people stopped can end level, and needs at least one finished game
    to end at all.
    """
    winner = match_winner(games, points_to, best_of)
    if best_of is not None:
        if winner is None:
            raise InvalidScore(
                f"The match can't be completed until a side has won {best_of // 2 + 1} games"
            )
        return winner
    if sum(games_won(games, points_to)) == 0:
        raise InvalidScore("The match can't be completed before a game is finished")
    return winner
