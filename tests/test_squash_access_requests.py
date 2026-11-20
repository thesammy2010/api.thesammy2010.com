"""Tests for asking to join the squash group, and reviewing those asks.

Like test_user_admin.py, these run against a real database, cleaning up
after themselves since the app's session is shared for the whole process.
"""

import uuid
from typing import Iterator

import pytest
from sqlalchemy import delete

from src.common import UserRole
from src.db import session
from src.models.squash import AccessRequest, Player
from src.models.user import User, UserAuditLog
from src.resolvers.squash.access_requests import (
    approve_request,
    create_request,
    decline_request,
    get_own_request,
    get_requests,
    withdraw_requests,
)
from src.resolvers.squash.players import Conflict, NotFound
from src.resolvers.users import delete_user_admin
from src.schemas.squash.access_requests import (
    AccessRequestRequest,
    ApproveAccessRequestRequest,
    ListAccessRequestsRequest,
)
from src.schemas.squash.enums import AccessRequestStatus


@pytest.fixture
def made() -> Iterator[dict]:
    """Deletes the users and players a test made, and their requests."""
    rows: dict = {"users": [], "players": []}
    yield rows
    users, players = rows["users"], rows["players"]
    session.rollback()
    session.execute(delete(AccessRequest).where(AccessRequest.user_id.in_(users)))
    players += [
        player_id
        for (player_id,) in session.query(Player.id).filter(Player.user_id.in_(users))
    ]
    session.execute(delete(Player).where(Player.id.in_(players)))
    session.execute(
        delete(UserAuditLog).where(
            UserAuditLog.actor_id.in_(users) | UserAuditLog.target_user_id.in_(users)
        )
    )
    session.execute(delete(User).where(User.id.in_(users)))
    session.commit()


@pytest.fixture
def new_user(made: dict):
    def make(role: UserRole = UserRole.GUEST, name: str = "Alex") -> User:
        email = f"test-{uuid.uuid4()}@example.com"
        user = User(google_account_id=email, email=email, name=name, role=role.value)
        session.add(user)
        session.commit()
        made["users"].append(user.id)
        return user

    return make


@pytest.fixture
def admin(new_user) -> User:
    return new_user(UserRole.ADMIN, name="Admin")


def ask(user: User, message: str = None) -> AccessRequest:
    return create_request(user, AccessRequestRequest(message=message))


class TestAsking:
    def test_a_guest_can_ask(self, new_user):
        user = new_user()

        made = ask(user, "  I play with Sam  ")

        assert made.status == AccessRequestStatus.PENDING.value
        assert made.message == "I play with Sam"
        assert get_own_request(user).id == made.id

    def test_only_one_can_be_waiting(self, new_user):
        user = new_user()
        ask(user)

        with pytest.raises(Conflict):
            ask(user)

    def test_a_player_cant_ask(self, new_user, made):
        user = new_user()
        player = Player(name="Alex", user_id=user.id)
        session.add(player)
        session.commit()

        with pytest.raises(Conflict):
            ask(user)

    def test_someone_added_by_email_cant_ask(self, new_user, made):
        user = new_user()
        player = Player(name="Alex", email=user.email)
        session.add(player)
        session.commit()
        made["players"].append(player.id)

        with pytest.raises(Conflict):
            ask(user)

    def test_someone_taken_out_of_the_group_can_ask_back(self, new_user):
        user = new_user()
        session.add(Player(name="Alex", user_id=user.id, is_active=False))
        session.commit()

        assert ask(user).status == AccessRequestStatus.PENDING.value


class TestWithdrawing:
    def test_withdrawing_deletes_the_request(self, new_user):
        user = new_user()
        ask(user)

        assert withdraw_requests(user)
        assert get_own_request(user) is None

    def test_nothing_to_withdraw(self, new_user):
        assert not withdraw_requests(new_user())

    def test_a_declined_request_can_be_cleared_and_asked_again(self, new_user, admin):
        user = new_user()
        decline_request(ask(user).id, admin)

        assert withdraw_requests(user)
        assert ask(user).status == AccessRequestStatus.PENDING.value

    def test_an_approved_request_is_kept(self, new_user, admin):
        user = new_user()
        approve_request(ask(user).id, admin, ApproveAccessRequestRequest())

        assert not withdraw_requests(user)
        assert get_own_request(user).status == AccessRequestStatus.APPROVED.value


class TestReviewing:
    def test_approving_adds_them_as_a_player(self, new_user, admin):
        user = new_user(name="Alex Smith")

        approved = approve_request(ask(user).id, admin, ApproveAccessRequestRequest())

        player = session.get(Player, approved.player_id)
        assert approved.status == AccessRequestStatus.APPROVED.value
        assert approved.reviewed_by_id == admin.id
        assert approved.reviewed_at is not None
        assert (player.name, player.email, player.user_id, player.is_active) == (
            "Alex Smith",
            user.email,
            user.id,
            True,
        )

    def test_approving_with_a_name(self, new_user, admin):
        user = new_user()

        approved = approve_request(
            ask(user).id, admin, ApproveAccessRequestRequest(name="Ali")
        )

        assert session.get(Player, approved.player_id).name == "Ali"

    def test_approving_as_someone_already_in_matches(self, new_user, admin, made):
        user = new_user()
        recorded = Player(name="Alex (guest)")
        session.add(recorded)
        session.commit()
        made["players"].append(recorded.id)

        approved = approve_request(
            ask(user).id, admin, ApproveAccessRequestRequest(player_id=recorded.id)
        )

        assert approved.player_id == recorded.id
        assert recorded.user_id == user.id

    def test_approving_as_someone_elses_player_is_refused(self, new_user, admin):
        user, other = new_user(), new_user()
        theirs = Player(name="Sam", user_id=other.id)
        session.add(theirs)
        session.commit()

        with pytest.raises(Conflict):
            approve_request(
                ask(user).id, admin, ApproveAccessRequestRequest(player_id=theirs.id)
            )

    def test_approving_brings_back_someone_who_left(self, new_user, admin):
        user = new_user()
        left = Player(name="Alex", user_id=user.id, is_active=False)
        session.add(left)
        session.commit()

        approved = approve_request(ask(user).id, admin, ApproveAccessRequestRequest())

        assert approved.player_id == left.id
        assert left.is_active

    def test_a_request_is_only_reviewed_once(self, new_user, admin):
        request_id = ask(new_user()).id
        decline_request(request_id, admin)

        with pytest.raises(Conflict):
            approve_request(request_id, admin, ApproveAccessRequestRequest())

    def test_an_unknown_request(self, admin):
        with pytest.raises(NotFound):
            decline_request(uuid.uuid4(), admin)

    def test_listing_by_status(self, new_user, admin):
        waiting, declined = ask(new_user()), ask(new_user())
        decline_request(declined.id, admin)

        pending = get_requests(
            ListAccessRequestsRequest(status=AccessRequestStatus.PENDING)
        )

        assert waiting.id in {r.id for r in pending}
        assert declined.id not in {r.id for r in pending}


class TestDeletingTheirAccount:
    def test_their_requests_go(self, new_user):
        user = new_user()
        request_id = ask(user).id

        delete_user_admin(actor=user, user_id=user.id)

        assert session.get(AccessRequest, request_id) is None
