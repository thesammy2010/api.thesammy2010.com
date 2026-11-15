"""Tests for the rules of a squash game and match."""

import pytest

from src.resolvers.squash.scoring import (
    InvalidScore,
    check_game_score,
    check_match_games,
    final_result,
    game_winner,
    games_won,
    match_winner,
    serving_side,
)


class TestGameWinner:
    @pytest.mark.parametrize(
        "side1,side2,winner",
        [
            (11, 0, 1),
            (9, 11, 2),
            (12, 10, 1),
            (15, 17, 2),
            (11, 10, None),
            (10, 10, None),
            (5, 3, None),
        ],
    )
    def test_first_to_11_unless_its_10_all(self, side1, side2, winner):
        assert game_winner(side1, side2, points_to=11) == winner

    def test_a_game_to_15(self):
        assert game_winner(11, 3, points_to=15) is None
        assert game_winner(15, 3, points_to=15) == 1


class TestCheckGameScore:
    @pytest.mark.parametrize(
        "side1,side2", [(0, 0), (11, 9), (10, 11), (12, 10), (13, 11), (6, 4)]
    )
    def test_scores_that_can_happen(self, side1, side2):
        check_game_score(side1, side2, points_to=11)

    @pytest.mark.parametrize("side1,side2", [(12, 5), (14, 11), (12, 9), (-1, 3)])
    def test_scores_play_would_have_stopped_before(self, side1, side2):
        with pytest.raises(InvalidScore):
            check_game_score(side1, side2, points_to=11)


class TestMatch:
    def test_games_won_ignores_one_still_being_played(self):
        assert games_won([(11, 5), (8, 11), (4, 2)], points_to=11) == (1, 1)

    def test_best_of_five_needs_three(self):
        games = [(11, 5), (8, 11), (11, 9)]

        assert match_winner(games, 11, best_of=5) is None
        assert match_winner(games + [(11, 2)], 11, best_of=5) == 1

    def test_without_best_of_the_most_games_wins(self):
        assert match_winner([(11, 5), (8, 11), (11, 9)], 11, best_of=None) == 1
        assert match_winner([(11, 5), (8, 11)], 11, best_of=None) is None

    def test_only_the_last_game_can_be_unfinished(self):
        with pytest.raises(InvalidScore, match="Game 1 is unfinished"):
            check_match_games([(5, 3), (11, 2)], 11, best_of=None)

    def test_no_game_after_the_match_is_won(self):
        with pytest.raises(InvalidScore, match="already won"):
            check_match_games([(11, 5), (11, 5), (0, 1)], 11, best_of=3)

    def test_no_more_games_than_best_of(self):
        check_match_games([(11, 5), (5, 11), (11, 5)], 11, best_of=3)
        with pytest.raises(InvalidScore):
            check_match_games([(11, 5)] * 2 + [(5, 11)] * 2, 11, best_of=3)


class TestServingSide:
    def test_the_rally_winner_serves_next(self):
        assert serving_side((3, 2), last_rally_won_by=2, points_to=11) == 2

    def test_the_game_winner_serves_first_in_the_next(self):
        assert serving_side((9, 11), last_rally_won_by=2, points_to=11) == 2
        # Even when the game's score was set without its rallies
        assert serving_side((11, 4), last_rally_won_by=None, points_to=11) == 1

    def test_unknown_before_the_first_rally(self):
        assert serving_side(None, last_rally_won_by=None, points_to=11) is None
        assert serving_side((3, 2), last_rally_won_by=None, points_to=11) is None


class TestFinalResult:
    def test_a_best_of_match_has_to_have_been_won(self):
        assert final_result([(11, 5), (11, 7)], 11, best_of=3) == 1
        with pytest.raises(InvalidScore, match="won 2 games"):
            final_result([(11, 5), (7, 11)], 11, best_of=3)

    def test_just_playing_games_the_side_with_more_wins(self):
        assert final_result([(11, 5), (7, 11), (5, 11)], 11, best_of=None) == 2

    def test_just_playing_games_level_is_a_draw(self):
        assert final_result([(11, 5), (7, 11)], 11, best_of=None) is None

    def test_a_game_left_unfinished_doesnt_count(self):
        """Out of court time at 7-5 in the third."""
        assert final_result([(11, 5), (7, 11), (7, 5)], 11, best_of=None) is None

    def test_it_cant_end_before_a_game_is_finished(self):
        with pytest.raises(InvalidScore, match="before a game is finished"):
            final_result([(7, 5)], 11, best_of=None)
