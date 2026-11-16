"""Tests for what a game's rallies show about how it was played."""

import uuid
from types import SimpleNamespace

from src.resolvers.squash.insights import (
    Tally,
    player_insights,
    replay_game,
    servers,
    went_to_deuce,
)

ME, THEM = uuid.uuid4(), uuid.uuid4()


class TestServers:
    def test_the_winner_of_each_rally_serves_the_next(self):
        assert servers([1, 1, 2, 1], [None] * 4, first=2) == [2, 1, 1, 2]

    def test_unknown_until_a_rally_is_won_without_a_first_server(self):
        assert servers([2, 1], [None, None], first=None) == [None, 2]

    def test_a_recorded_server_is_taken_as_it_is(self):
        assert servers([1, 1], [None, 2], first=None) == [None, 2]


class TestWentToDeuce:
    def test_10_all_is_deuce_in_a_game_to_11(self):
        assert went_to_deuce(12, 10, 11)
        assert not went_to_deuce(11, 9, 11)


class TestReplayGame:
    def test_serve_and_receive_are_counted_from_each_side(self):
        # Side 1 serves first and wins, serves again and loses, then side 2
        # serves and wins
        replay = replay_game([1, 2, 2], servers([1, 2, 2], [None] * 3, 1), 11)

        assert (replay.tallies[1].serves_played, replay.tallies[1].serves_won) == (2, 1)
        assert (replay.tallies[2].serves_played, replay.tallies[2].serves_won) == (1, 1)
        assert replay.tallies[2].receives_won == 1
        assert replay.tallies[2].longest_run == 2

    def test_a_comeback_from_0_5_to_11_5(self):
        won_by = [2] * 5 + [1] * 11
        replay = replay_game(won_by, [None] * len(won_by), 11)

        assert replay.deepest_deficit[1] == 5
        assert replay.tallies[1].longest_run == 11
        assert replay.tallies[1].biggest_lead == 6
        assert replay.tallies[2].biggest_lead == 5

    def test_game_points(self):
        # From 8-all to 10-8, side 2 saves one game point, then side 1 takes
        # the next
        won_by = [1, 2] * 8 + [1, 1, 2, 1]
        replay = replay_game(won_by, [None] * len(won_by), 11)

        assert (replay.tallies[1].game_points, replay.tallies[1].game_points_won) == (
            2,
            1,
        )
        assert replay.tallies[2].game_points == 0


class TestTally:
    def test_runs_and_leads_take_the_best_and_counts_add_up(self):
        tally = Tally(rallies_won=3, longest_run=4, biggest_lead=2)
        tally.add(Tally(rallies_won=5, longest_run=2, biggest_lead=6))

        assert (tally.rallies_won, tally.longest_run, tally.biggest_lead) == (8, 4, 6)


def _game(*won_by, side1=None, side2=None):
    rallies = [SimpleNamespace(won_by_side=won, server_id=None) for won in won_by]
    return SimpleNamespace(
        side1_points=won_by.count(1) if side1 is None else side1,
        side2_points=won_by.count(2) if side2 is None else side2,
        rallies=rallies,
    )


def _match(*games, my_side=1):
    return SimpleNamespace(
        points_to=11,
        players=[
            SimpleNamespace(player_id=ME, side=my_side),
            SimpleNamespace(player_id=THEM, side=3 - my_side),
        ],
        games=list(games),
    )


class TestPlayerInsights:
    def test_counted_from_the_players_side(self):
        lead_lost = _game(*([2] * 4 + [1] * 11))
        comeback = _game(*([1] * 5 + [2] * 11))
        insights = player_insights([_match(lead_lost, comeback, my_side=2)], ME)

        # As side 2: lost the first after leading 4-0, won the second from 0-5
        assert insights.games_scored_live == 2
        assert (insights.comebacks, insights.biggest_comeback) == (1, 5)
        assert insights.leads_lost == 1
        assert insights.tally.rallies_won == 4 + 11

    def test_deuce_games_count_without_rallies(self):
        entered = _game(side1=12, side2=10)
        insights = player_insights([_match(entered)], ME)

        assert insights.games_scored_live == 0
        assert (insights.deuce_games_won, insights.deuce_games_lost) == (1, 0)
