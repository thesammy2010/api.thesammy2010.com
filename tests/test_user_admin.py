"""Tests over user provisioning, admin management, and soft-delete.

These run against a real database (see conftest.py in CI, or a local
Postgres for `pytest` run by hand) rather than mocks, since the behaviour
under test - the partial unique index, and the shared session picking up
committed changes without a restart - only shows up against a real engine.
"""

import uuid
from typing import Iterator, List

import pytest
from pydantic import ValidationError
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from src.common import UserRole
from src.db import session
from src.models.user import User, UserAuditLog
from src.resolvers.users import (
    create_user_admin,
    create_user_in_db,
    delete_user_admin,
    find_user_by_claims,
    list_users,
    set_user_role,
)
from src.schemas.users import CreateUserRequest, ListUsersRequest


@pytest.fixture
def track_users() -> Iterator[List[uuid.UUID]]:
    """Deletes every user (and their audit log rows) created by a test.

    The app's session is a single instance shared for the whole process
    (see src/db.py), so tests can't rely on a per-test transaction to undo
    what they wrote - they have to clean up explicitly instead.
    """
    ids: List[uuid.UUID] = []
    yield ids
    if ids:
        session.execute(
            delete(UserAuditLog).where(
                UserAuditLog.actor_id.in_(ids) | UserAuditLog.target_user_id.in_(ids)
            )
        )
        session.execute(delete(User).where(User.id.in_(ids)))
        session.commit()


@pytest.fixture
def admin_user(track_users: List[uuid.UUID]) -> User:
    """A real admin row to attribute audit log entries to."""
    user = User(google_account_id=f"admin-{uuid.uuid4()}", role=UserRole.ADMIN.value)
    session.add(user)
    session.commit()
    track_users.append(user.id)
    return user


def google_account_id() -> str:
    return f"test-{uuid.uuid4()}"


def email_address() -> str:
    return f"test-{uuid.uuid4()}@example.com"


class TestProvisioning:
    """Test create_user_in_db / find_user_by_claims, the self-service path."""

    def test_a_new_google_account_is_provisioned_as_guest(
        self, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()

        user = create_user_in_db({"sub": sub})
        track_users.append(user.id)

        assert user.role == UserRole.GUEST.value

    def test_provisioning_the_same_account_twice_returns_one_row(
        self, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()
        first = create_user_in_db({"sub": sub})
        track_users.append(first.id)

        second = create_user_in_db({"sub": sub})

        assert second.id == first.id

    def test_provisioning_writes_a_created_audit_log_entry(
        self, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()

        user = create_user_in_db({"sub": sub})
        track_users.append(user.id)

        entry = (
            session.query(UserAuditLog).where(UserAuditLog.target_user_id == user.id)
        ).one()
        assert entry.action == "created"

    def test_a_deleted_user_is_not_found_by_their_claims(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()
        user = create_user_in_db({"sub": sub})
        track_users.append(user.id)
        delete_user_admin(actor=admin_user, user_id=user.id)

        assert find_user_by_claims({"sub": sub}) is None

    def test_provisioning_stores_email_and_name_from_claims(
        self, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()

        user = create_user_in_db(
            {"sub": sub, "email": "ada@example.com", "name": "Ada Lovelace"}
        )
        track_users.append(user.id)

        assert user.email == "ada@example.com"
        assert user.name == "Ada Lovelace"

    def test_signing_in_again_refreshes_email_and_name(
        self, track_users: List[uuid.UUID]
    ):
        """The Google account is the source of truth, so a rename there
        should be picked up on the next sign-in."""
        sub = google_account_id()
        create_user_in_db({"sub": sub, "email": "old@example.com", "name": "Old Name"})

        updated = create_user_in_db(
            {"sub": sub, "email": "new@example.com", "name": "New Name"}
        )
        track_users.append(updated.id)

        assert updated.email == "new@example.com"
        assert updated.name == "New Name"

    def test_provisioning_sets_last_signed_in_at(self, track_users: List[uuid.UUID]):
        user = create_user_in_db({"sub": google_account_id()})
        track_users.append(user.id)

        assert user.last_signed_in_at is not None

    def test_signing_in_again_bumps_last_signed_in_at(
        self, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()
        first = create_user_in_db({"sub": sub})
        track_users.append(first.id)
        first_seen = first.last_signed_in_at

        second = create_user_in_db({"sub": sub})

        assert second.last_signed_in_at is not None
        assert second.last_signed_in_at >= first_seen

    def test_signing_in_again_after_deletion_provisions_a_fresh_row(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        """The deleted row is not revived - it stays deleted, and a new one
        takes over the now-freed google_account_id."""
        sub = google_account_id()
        original = create_user_in_db({"sub": sub})
        track_users.append(original.id)
        delete_user_admin(actor=admin_user, user_id=original.id)

        reprovisioned = create_user_in_db({"sub": sub})
        track_users.append(reprovisioned.id)

        assert reprovisioned.id != original.id
        assert reprovisioned.role == UserRole.GUEST.value


class TestCreateUserAdmin:
    """Test the admin pre-provisioning endpoint's resolver."""

    def test_an_admin_can_pre_provision_an_account_with_a_role(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()

        user = create_user_admin(
            actor=admin_user, google_account_id=sub, role=UserRole.EDITOR
        )
        track_users.append(user.id)

        assert user.role == UserRole.EDITOR.value

    def test_pre_provisioning_leaves_last_signed_in_at_unset(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        """Nobody has actually signed in yet - only create_user_in_db,
        the self-service path, stamps this."""
        user = create_user_admin(
            actor=admin_user,
            google_account_id=google_account_id(),
            role=UserRole.VIEWER,
        )
        track_users.append(user.id)

        assert user.last_signed_in_at is None

    def test_pre_provisioning_can_label_the_account_with_an_email_and_name(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        user = create_user_admin(
            actor=admin_user,
            google_account_id=google_account_id(),
            role=UserRole.VIEWER,
            email="invited@example.com",
            name="Invited Person",
        )
        track_users.append(user.id)

        assert user.email == "invited@example.com"
        assert user.name == "Invited Person"

    def test_signing_in_overwrites_the_admin_supplied_label(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()
        create_user_admin(
            actor=admin_user,
            google_account_id=sub,
            role=UserRole.VIEWER,
            email="guess@example.com",
            name="Guessed Name",
        )

        signed_in = create_user_in_db(
            {"sub": sub, "email": "real@example.com", "name": "Real Name"}
        )
        track_users.append(signed_in.id)

        assert signed_in.email == "real@example.com"
        assert signed_in.name == "Real Name"

    def test_pre_provisioning_an_already_active_account_returns_none(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()
        existing = create_user_in_db({"sub": sub})
        track_users.append(existing.id)

        result = create_user_admin(
            actor=admin_user, google_account_id=sub, role=UserRole.VIEWER
        )

        assert result is None

    def test_pre_provisioning_after_the_prior_account_was_deleted_succeeds(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()
        original = create_user_in_db({"sub": sub})
        track_users.append(original.id)
        delete_user_admin(actor=admin_user, user_id=original.id)

        reinvited = create_user_admin(
            actor=admin_user, google_account_id=sub, role=UserRole.VIEWER
        )
        track_users.append(reinvited.id)

        assert reinvited is not None
        assert reinvited.id != original.id

    def test_pre_provisioning_writes_a_created_audit_log_entry_with_the_role(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()

        user = create_user_admin(
            actor=admin_user, google_account_id=sub, role=UserRole.EDITOR
        )
        track_users.append(user.id)

        entry = (
            session.query(UserAuditLog).where(UserAuditLog.target_user_id == user.id)
        ).one()
        assert entry.action == "created"
        assert entry.actor_id == admin_user.id
        assert entry.new_role == UserRole.EDITOR.value

    def test_an_admin_can_pre_provision_by_email_alone(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        user = create_user_admin(
            actor=admin_user, role=UserRole.VIEWER, email=email_address()
        )
        track_users.append(user.id)

        assert user.google_account_id is None

    def test_pre_provisioning_conflicts_on_a_matching_active_email_too(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        email = email_address()
        existing = create_user_in_db({"sub": google_account_id(), "email": email})
        track_users.append(existing.id)

        result = create_user_admin(actor=admin_user, role=UserRole.VIEWER, email=email)

        assert result is None


class TestClaimByEmail:
    """Test that a first sign-in claims a matching email-only placeholder
    instead of creating a second, default-GUEST row."""

    def test_signing_in_claims_a_matching_placeholder(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        email = email_address()
        placeholder = create_user_admin(
            actor=admin_user, role=UserRole.EDITOR, email=email
        )
        track_users.append(placeholder.id)

        signed_in = create_user_in_db(
            {"sub": google_account_id(), "email": email, "name": "Real Name"}
        )

        assert signed_in.id == placeholder.id

    def test_claiming_keeps_the_role_the_admin_set(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        email = email_address()
        placeholder = create_user_admin(
            actor=admin_user, role=UserRole.EDITOR, email=email
        )
        track_users.append(placeholder.id)

        signed_in = create_user_in_db(
            {"sub": google_account_id(), "email": email, "name": "Real Name"}
        )

        assert signed_in.role == UserRole.EDITOR.value

    def test_claiming_fills_in_the_google_account_id_and_name(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        email = email_address()
        placeholder = create_user_admin(
            actor=admin_user, role=UserRole.EDITOR, email=email, name="Guessed Name"
        )
        track_users.append(placeholder.id)
        sub = google_account_id()

        signed_in = create_user_in_db({"sub": sub, "email": email, "name": "Real Name"})

        assert signed_in.google_account_id == sub
        assert signed_in.name == "Real Name"

    def test_claiming_writes_a_claimed_audit_log_entry(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        email = email_address()
        placeholder = create_user_admin(
            actor=admin_user, role=UserRole.EDITOR, email=email
        )
        track_users.append(placeholder.id)

        create_user_in_db({"sub": google_account_id(), "email": email})

        entry = (
            session.query(UserAuditLog).where(
                UserAuditLog.target_user_id == placeholder.id,
                UserAuditLog.action == "claimed",
            )
        ).one()
        assert entry.actor_id == placeholder.id

    def test_signing_in_with_no_matching_placeholder_creates_a_new_guest_row(
        self, track_users: List[uuid.UUID]
    ):
        user = create_user_in_db({"sub": google_account_id(), "email": email_address()})
        track_users.append(user.id)

        assert user.role == UserRole.GUEST.value


class TestCreateUserRequestValidation:
    """CreateUserRequest needs at least one way to identify who it's for."""

    def test_neither_google_account_id_nor_email_is_rejected(self):
        with pytest.raises(ValidationError):
            CreateUserRequest(role=UserRole.GUEST)

    def test_email_alone_is_accepted(self):
        CreateUserRequest(role=UserRole.GUEST, email=email_address())

    def test_google_account_id_alone_is_accepted(self):
        CreateUserRequest(role=UserRole.GUEST, google_account_id=google_account_id())


class TestDeleteUserAdmin:
    """Test soft-deletion: the row is marked, never removed."""

    def test_deleting_sets_deleted_at_rather_than_removing_the_row(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        user = create_user_in_db({"sub": google_account_id()})
        track_users.append(user.id)

        deleted = delete_user_admin(actor=admin_user, user_id=user.id)

        assert deleted is not None
        assert deleted.deleted_at is not None
        assert session.get(User, user.id) is not None

    def test_deleting_an_already_deleted_user_returns_none(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        user = create_user_in_db({"sub": google_account_id()})
        track_users.append(user.id)
        delete_user_admin(actor=admin_user, user_id=user.id)

        assert delete_user_admin(actor=admin_user, user_id=user.id) is None

    def test_deleting_an_unknown_user_returns_none(self, admin_user: User):
        assert delete_user_admin(actor=admin_user, user_id=uuid.uuid4()) is None

    def test_deleting_writes_a_deleted_audit_log_entry(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        user = create_user_in_db({"sub": google_account_id()})
        track_users.append(user.id)

        delete_user_admin(actor=admin_user, user_id=user.id)

        entry = (
            session.query(UserAuditLog).where(
                UserAuditLog.target_user_id == user.id,
                UserAuditLog.action == "deleted",
            )
        ).one()
        assert entry.actor_id == admin_user.id


class TestListUsers:
    """Test the admin listing - deleted_at isn't exposed at the API level,
    so a deleted user must be excluded rather than shown indistinguishably
    from an active one."""

    def test_an_active_user_is_listed(self, track_users: List[uuid.UUID]):
        user = create_user_in_db({"sub": google_account_id()})
        track_users.append(user.id)

        listed_ids = {u.id for u in list_users(ListUsersRequest())}

        assert user.id in listed_ids

    def test_a_deleted_user_is_not_listed(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        user = create_user_in_db({"sub": google_account_id()})
        track_users.append(user.id)
        delete_user_admin(actor=admin_user, user_id=user.id)

        listed_ids = {u.id for u in list_users(ListUsersRequest())}

        assert user.id not in listed_ids


class TestSetUserRole:
    """Test admin-driven role changes and their visibility/audit trail."""

    def test_changing_role_updates_it(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        user = create_user_in_db({"sub": google_account_id()})
        track_users.append(user.id)

        updated = set_user_role(actor=admin_user, user_id=user.id, role=UserRole.EDITOR)

        assert updated.role == UserRole.EDITOR.value

    def test_the_change_is_visible_without_a_restart(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        """Regression test for the staleness bug: the shared session must
        not keep serving the pre-change role from its identity map."""
        user = create_user_in_db({"sub": google_account_id()})
        track_users.append(user.id)

        set_user_role(actor=admin_user, user_id=user.id, role=UserRole.EDITOR)

        assert session.get(User, user.id).role == UserRole.EDITOR.value

    def test_changing_role_of_an_unknown_user_returns_none(self, admin_user: User):
        result = set_user_role(
            actor=admin_user, user_id=uuid.uuid4(), role=UserRole.EDITOR
        )

        assert result is None

    def test_changing_role_of_a_deleted_user_returns_none(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        user = create_user_in_db({"sub": google_account_id()})
        track_users.append(user.id)
        delete_user_admin(actor=admin_user, user_id=user.id)

        result = set_user_role(actor=admin_user, user_id=user.id, role=UserRole.EDITOR)

        assert result is None

    def test_changing_role_writes_the_previous_and_new_role_to_the_audit_log(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        user = create_user_in_db({"sub": google_account_id()})
        track_users.append(user.id)

        set_user_role(actor=admin_user, user_id=user.id, role=UserRole.EDITOR)

        entry = (
            session.query(UserAuditLog).where(
                UserAuditLog.target_user_id == user.id,
                UserAuditLog.action == "role_changed",
            )
        ).one()
        assert entry.previous_role == UserRole.GUEST.value
        assert entry.new_role == UserRole.EDITOR.value


class TestSelfDelete:
    """Test the composition DELETE /users uses: find_user_by_claims then
    delete_user_admin with the caller as their own actor."""

    def test_a_user_can_delete_their_own_account(self, track_users: List[uuid.UUID]):
        sub = google_account_id()
        user = create_user_in_db({"sub": sub})
        track_users.append(user.id)

        deleted = delete_user_admin(actor=user, user_id=user.id)

        assert deleted is not None
        assert deleted.deleted_at is not None

    def test_a_self_deleted_account_is_gone_from_their_own_claims_lookup(
        self, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()
        user = create_user_in_db({"sub": sub})
        track_users.append(user.id)
        delete_user_admin(actor=user, user_id=user.id)

        assert find_user_by_claims({"sub": sub}) is None

    def test_self_deletion_is_attributed_to_the_deleted_user_themselves(
        self, track_users: List[uuid.UUID]
    ):
        user = create_user_in_db({"sub": google_account_id()})
        track_users.append(user.id)

        delete_user_admin(actor=user, user_id=user.id)

        entry = (
            session.query(UserAuditLog).where(
                UserAuditLog.target_user_id == user.id,
                UserAuditLog.action == "deleted",
            )
        ).one()
        assert entry.actor_id == user.id


class TestGoogleAccountIdConstraint:
    """Test the partial unique index backing the soft-delete design."""

    def test_two_active_users_cannot_share_a_google_account_id(
        self, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()
        first = User(google_account_id=sub)
        session.add(first)
        session.commit()
        track_users.append(first.id)

        second = User(google_account_id=sub)
        session.add(second)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_a_deleted_and_an_active_user_can_share_a_google_account_id(
        self, admin_user: User, track_users: List[uuid.UUID]
    ):
        sub = google_account_id()
        original = create_user_in_db({"sub": sub})
        track_users.append(original.id)
        delete_user_admin(actor=admin_user, user_id=original.id)

        replacement = User(google_account_id=sub)
        session.add(replacement)
        session.commit()
        track_users.append(replacement.id)

        assert replacement.id != original.id
