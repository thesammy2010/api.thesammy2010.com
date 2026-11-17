"""What the rallies of games scored live say about how they were played.

Kept free of any database import so that it stays unit testable. A game
whose score was entered whole has no rallies, so it only counts towards what
its final score shows, such as whether it went to deuce.
"""

import dataclasses
import uuid
from typing import Dict, List, Optional, Sequence

from src.resolvers.squash import scoring
from src.resolvers.squash.scoring import SIDES

# Winning a game from this many points down or more counts as a comeback
COMEBACK_DEFICIT = 3
# The Tally field each RallyDecision value is counted in
CALLS = {"let": "lets", "stroke": "strokes", "no_let": "no_lets"}


@dataclasses.dataclass
class Tally:
    """One side's rallies, over a game or added up over several."""

    rallies_played: int = 0
    rallies_won: int = 0
    # Only rallies whose server is known: recorded, or worked out from who
    # won the rally before
    serves_played: int = 0
    serves_won: int = 0
    receives_played: int = 0
    receives_won: int = 0
    longest_run: int = 0
    biggest_lead: int = 0
    # Rallies that would have won the game
    game_points: int = 0
    game_points_won: int = 0
    # Their appeals, by the call made. Lets are only counted for a side when
    # who appealed was recorded
    lets: int = 0
    strokes: int = 0
    no_lets: int = 0

    def add(self, other: "Tally") -> None:
        for field in dataclasses.fields(self):
            mine, theirs = getattr(self, field.name), getattr(other, field.name)
            if field.name in ("longest_run", "biggest_lead"):
                setattr(self, field.name, max(mine, theirs))
            else:
                setattr(self, field.name, mine + theirs)


@dataclasses.dataclass
class GameReplay:
    tallies: Dict[int, Tally]
    # The most each side was ever behind by
    deepest_deficit: Dict[int, int]
    # Every let, whoever appealed
    lets: int = 0


def went_to_deuce(side1: int, side2: int, points_to: int) -> bool:
    """Whether a game reached one point short all, such as 10-10, after which
    it goes on until a side is two clear."""
    return min(side1, side2) >= points_to - 1


def servers(
    won_by: Sequence[int], recorded: Sequence[Optional[int]], first: Optional[int]
) -> List[Optional[int]]:
    """The side that served each rally, or None where there's no telling.

    A recorded server is taken as it is. Otherwise the winner of each rally
    serves the next, under point-a-rally, and first is the side serving the
    first rally: the winner of the game before, or None for the first game.
    """
    sides: List[Optional[int]] = []
    serving = first
    for won, server in zip(won_by, recorded):
        if server is not None:
            serving = server
        sides.append(serving)
        serving = won
    return sides


def replay_game(
    won_by: Sequence[int], server_sides: Sequence[Optional[int]], points_to: int
) -> GameReplay:
    """Goes through a game rally by rally, keeping count for each side."""
    tallies = {side: Tally() for side in SIDES}
    points = {side: 0 for side in SIDES}
    deficit = {side: 0 for side in SIDES}
    run_side, run = None, 0
    for won, server in zip(won_by, server_sides):
        for side in SIDES:
            tally, mine, theirs = tallies[side], points[side], points[3 - side]
            tally.rallies_played += 1
            # Winning this rally would leave them on points_to or more, two clear
            if mine >= points_to - 1 and mine > theirs:
                tally.game_points += 1
                tally.game_points_won += won == side
            if server == side:
                tally.serves_played += 1
                tally.serves_won += won == side
            elif server is not None:
                tally.receives_played += 1
                tally.receives_won += won == side

        points[won] += 1
        tallies[won].rallies_won += 1
        run = run + 1 if won == run_side else 1
        run_side = won
        tallies[won].longest_run = max(tallies[won].longest_run, run)
        for side in SIDES:
            lead = points[side] - points[3 - side]
            tallies[side].biggest_lead = max(tallies[side].biggest_lead, lead)
            deficit[side] = max(deficit[side], -lead)
    return GameReplay(tallies=tallies, deepest_deficit=deficit)


def replay_match(match) -> List[Optional[GameReplay]]:
    """Each game's replay in order, or None for one not scored live.

    Lets are left out of the points, being replayed, but counted with the
    strokes and no lets as the calls each side's appeals got.
    """
    player_sides = {player.player_id: player.side for player in match.players}
    replays: List[Optional[GameReplay]] = []
    previous_winner = None
    for game in match.games:
        if game.rallies:
            points = [rally for rally in game.rallies if rally.won_by_side]
            won_by = [rally.won_by_side for rally in points]
            recorded = [player_sides.get(rally.server_id) for rally in points]
            replay = replay_game(
                won_by, servers(won_by, recorded, previous_winner), match.points_to
            )
            for rally in game.rallies:
                replay.lets += rally.decision == "let"
                if rally.decision and rally.appealed_by_side:
                    tally = replay.tallies[rally.appealed_by_side]
                    name = CALLS[rally.decision]
                    setattr(tally, name, getattr(tally, name) + 1)
            replays.append(replay)
        else:
            replays.append(None)
        previous_winner = scoring.game_winner(
            game.side1_points, game.side2_points, match.points_to
        )
    return replays


@dataclasses.dataclass
class PlayerInsights:
    tally: Tally = dataclasses.field(default_factory=Tally)
    games_scored_live: int = 0
    # Live games won from COMEBACK_DEFICIT or more down, and lost from as far
    # up
    comebacks: int = 0
    biggest_comeback: int = 0
    leads_lost: int = 0
    deuce_games_won: int = 0
    deuce_games_lost: int = 0


def player_insights(matches, player_id: uuid.UUID) -> PlayerInsights:
    """What a player's matches say about how they play, from their side."""
    insights = PlayerInsights()
    for match in matches:
        side = next((p.side for p in match.players if p.player_id == player_id), None)
        if side is None:
            continue
        for game, replay in zip(match.games, replay_match(match)):
            winner = scoring.game_winner(
                game.side1_points, game.side2_points, match.points_to
            )
            if winner and went_to_deuce(
                game.side1_points, game.side2_points, match.points_to
            ):
                insights.deuce_games_won += winner == side
                insights.deuce_games_lost += winner != side
            if replay is None:
                continue
            insights.games_scored_live += 1
            insights.tally.add(replay.tallies[side])
            if winner == side and replay.deepest_deficit[side] >= COMEBACK_DEFICIT:
                insights.comebacks += 1
                insights.biggest_comeback = max(
                    insights.biggest_comeback, replay.deepest_deficit[side]
                )
            elif winner == 3 - side and (
                replay.deepest_deficit[3 - side] >= COMEBACK_DEFICIT
            ):
                insights.leads_lost += 1
    return insights
