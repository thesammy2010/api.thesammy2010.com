"""Tests for registering phones for notifications.

Against a real database, like test_user_admin.py, cleaning up after
themselves since the app's session is shared for the whole process.
"""

import uuid
from typing import Iterator, List

import pytest
from pydantic import ValidationError
from sqlalchemy import delete

from src.db import session
from src.models.device import Device
from src.models.user import User, UserAuditLog
from src.resolvers.devices import get_devices, register_device, unregister_device
from src.resolvers.users import delete_user_admin
from src.schemas.devices import DeviceEnvironment, DeviceRequest

APP = "com.thesammy2010.how2squash.app"


@pytest.fixture
def made() -> Iterator[List[uuid.UUID]]:
    """Deletes the users a test made, and their devices."""
    users: List[uuid.UUID] = []
    yield users
    session.rollback()
    session.execute(delete(Device).where(Device.user_id.in_(users)))
    session.execute(
        delete(UserAuditLog).where(
            UserAuditLog.actor_id.in_(users) | UserAuditLog.target_user_id.in_(users)
        )
    )
    session.execute(delete(User).where(User.id.in_(users)))
    session.commit()


@pytest.fixture
def new_user(made: List[uuid.UUID]):
    def make() -> User:
        user = User(google_account_id=f"test-{uuid.uuid4()}")
        session.add(user)
        session.commit()
        made.append(user.id)
        return user

    return make


def token() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex


def request(value: str, environment=DeviceEnvironment.PRODUCTION) -> DeviceRequest:
    return DeviceRequest(token=value, app=APP, environment=environment)


class TestRegistering:
    def test_a_phone_is_registered(self, new_user):
        user = new_user()

        device = register_device(user, request(token()))

        assert device.user_id == user.id
        assert device.app == APP
        assert get_devices(user) == [device]

    def test_registering_again_refreshes_it(self, new_user):
        user, value = new_user(), token()
        first = register_device(user, request(value, DeviceEnvironment.SANDBOX))
        seen = first.last_registered_at

        again = register_device(user, request(value.upper()))

        assert again.id == first.id
        assert again.environment == DeviceEnvironment.PRODUCTION.value
        assert again.last_registered_at >= seen
        assert len(get_devices(user)) == 1

    def test_a_phone_signed_in_as_someone_else_moves_to_them(self, new_user):
        before, after, value = new_user(), new_user(), token()
        register_device(before, request(value))

        register_device(after, request(value))

        assert get_devices(before) == []
        assert [d.token for d in get_devices(after)] == [value]


class TestUnregistering:
    def test_signing_out_forgets_it(self, new_user):
        user, value = new_user(), token()
        register_device(user, request(value))

        assert unregister_device(user, value.upper())
        assert get_devices(user) == []

    def test_only_your_own(self, new_user):
        owner, other, value = new_user(), new_user(), token()
        register_device(owner, request(value))

        assert not unregister_device(other, value)
        assert len(get_devices(owner)) == 1

    def test_deleting_the_account_forgets_its_phones(self, new_user):
        user = new_user()
        register_device(user, request(token()))

        delete_user_admin(actor=user, user_id=user.id)

        assert session.query(Device).filter(Device.user_id == user.id).count() == 0


class TestRequest:
    @pytest.mark.parametrize("value", ["", "abc", "z" * 64, "0" * 63, "0" * 201])
    def test_a_token_must_be_hex_of_a_token_length(self, value):
        with pytest.raises(ValidationError):
            request(value)

    @pytest.mark.parametrize("app", ["", "how2squash", "com.thesammy2010.app/x"])
    def test_the_app_must_be_a_bundle_id(self, app):
        with pytest.raises(ValidationError):
            DeviceRequest(token=token(), app=app, environment="production")

    def test_the_token_is_kept_lowercase(self):
        assert request("AB" * 32).token == "ab" * 32
