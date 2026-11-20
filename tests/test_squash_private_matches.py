"""Tests for private matches, which only admins and their players see in
full. Against a real database, like test_squash_access_requests.py."""

import uuid
from typing import Iterator

import pytest
from sqlalchemy import delete

from src.common import UserRole
from src.db import session
from src.models.squash import Match, Player, Venue
from src.models.user import User
from src.resolvers.squash import matches, reports, stats
from src.resolvers.squash.players import NotAllowed, SquashCaller
from src.schemas.squash.enums import MatchFormat, MatchStatus
from src.schemas.squash.insights import RatingsRequest
from src.schemas.squash.matches import (
    GameRequest,
    ListMatchesRequest,
    MatchPlayerRequest,
    MatchRequest,
)


@pytest.fixture
def group() -> Iterator[dict]:
    """Alex and Sam, who play a private match, Kim, who doesn't, and an
    admin who doesn't play. Everything they made is deleted afterwards."""
    users, players = {}, {}
    for name, role in (
        ("alex", UserRole.GUEST),
        ("sam", UserRole.GUEST),
        ("kim", UserRole.GUEST),
        ("admin", UserRole.ADMIN),
    ):
        user = User(google_account_id=f"{name}-{uuid.uuid4()}", role=role.value)
        session.add(user)
        users[name] = user
    session.flush()
    for name in ("alex", "sam", "kim"):
        player = Player(name=name, user_id=users[name].id)
        session.add(player)
        players[name] = player
    session.commit()

    callers = {
        name: SquashCaller(user=users[name], player=players.get(name)) for name in users
    }
    yield {"callers": callers, "players": players}

    user_ids = [user.id for user in users.values()]
    session.rollback()
    session.execute(delete(Match).where(Match.created_by_id.in_(user_ids)))
    session.execute(delete(Player).where(Player.user_id.in_(user_ids)))
    session.execute(delete(User).where(User.id.in_(user_ids)))
    session.commit()


def _played(group, *, private: bool, by: str = "alex") -> Match:
    """A completed best of 1 that Alex won 11-5 against Sam."""
    players = group["players"]
    caller = group["callers"][by]
    match = matches.create_match(
        MatchRequest(
            format=MatchFormat.SINGLES,
            best_of=1,
            notes="Court 3",
            is_private=private,
            players=[
                MatchPlayerRequest(player_id=players["alex"].id, side=1),
                MatchPlayerRequest(player_id=players["sam"].id, side=2),
            ],
        ),
        caller,
    )
    matches.set_game(match.id, 1, GameRequest(side1_points=11, side2_points=5), caller)
    assert match.status == MatchStatus.COMPLETED.value
    return match


class TestSeeing:
    @pytest.mark.parametrize("who", ["alex", "sam", "admin"])
    def test_its_players_and_admins_see_it_all(self, group, who):
        match = _played(group, private=True)

        shown = matches.to_response(match, group["callers"][who])

        assert not shown.hidden
        assert (shown.winning_side, shown.notes, len(shown.games)) == (1, "Court 3", 1)

    def test_anyone_else_sees_only_who_played(self, group):
        match = _played(group, private=True)

        shown = matches.to_response(match, group["callers"]["kim"])

        assert shown.hidden and shown.is_private
        assert {p.player_id for p in shown.players} == {
            group["players"]["alex"].id,
            group["players"]["sam"].id,
        }
        assert shown.games == []
        assert (shown.winning_side, shown.side1_games, shown.notes) == (
            None,
            None,
            None,
        )

    def test_a_match_that_isnt_private_is_seen_by_everyone(self, group):
        match = _played(group, private=False)

        assert not matches.to_response(match, group["callers"]["kim"]).hidden

    def test_its_rallies_are_refused(self, group):
        match = _played(group, private=True)

        with pytest.raises(NotAllowed):
            matches.check_can_see(match, group["callers"]["kim"])

    def test_it_isnt_found_by_its_venue(self, group):
        """Its venue is hidden, so filtering by venue mustn't reveal it."""
        venue = Venue(name=f"Club {uuid.uuid4()}")
        session.add(venue)
        match = _played(group, private=True)
        match.venue = venue
        session.commit()
        try:
            for who, expected in (("kim", False), ("sam", True), ("admin", True)):
                found = matches.get_matches(
                    ListMatchesRequest(venue_id=venue.id), group["callers"][who]
                )
                assert (match.id in {m.id for m in found}) == expected, who
        finally:
            match.venue = None
            session.delete(venue)
            session.commit()


class TestChanging:
    def test_someone_not_in_it_cant_change_it_even_having_arranged_it(self, group):
        players, kim = group["players"], group["callers"]["kim"]
        match = matches.create_match(
            MatchRequest(
                format=MatchFormat.SINGLES,
                is_private=True,
                players=[
                    MatchPlayerRequest(player_id=players["alex"].id, side=1),
                    MatchPlayerRequest(player_id=players["sam"].id, side=2),
                ],
            ),
            kim,
        )

        with pytest.raises(NotAllowed):
            matches.set_game(
                match.id, 1, GameRequest(side1_points=11, side2_points=5), kim
            )
        with pytest.raises(NotAllowed):
            matches.delete_match(match.id, kim)

    def test_its_players_can(self, group):
        match = _played(group, private=True)

        assert matches.delete_match(match.id, group["callers"]["sam"])


class TestCounting:
    def test_stats_count_it_only_for_those_who_can_see_it(self, group):
        _played(group, private=True)
        alex = group["players"]["alex"].id

        for who, expected in (("alex", 1), ("sam", 1), ("admin", 1), ("kim", 0)):
            record = stats.get_player_stats(alex, group["callers"][who])
            assert record.matches_played == expected, who

    def test_head_to_head_too(self, group):
        _played(group, private=True)
        alex, sam = group["players"]["alex"].id, group["players"]["sam"].id

        assert (
            stats.get_head_to_head(alex, sam, group["callers"]["kim"]).matches_played
            == 0
        )
        assert (
            stats.get_head_to_head(alex, sam, group["callers"]["sam"]).matches_played
            == 1
        )

    def test_ratings_leave_it_out_for_everyone(self, group):
        _played(group, private=True)
        rated = {r.player_id for r in reports.get_ratings(RatingsRequest())}

        assert group["players"]["alex"].id not in rated
        assert reports.get_rating_history(group["players"]["alex"].id, None) == []
