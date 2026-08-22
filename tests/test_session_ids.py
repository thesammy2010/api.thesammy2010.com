import datetime
import uuid

import pytest

from src.migration_utils.session_ids import (
    SESSION_NAMESPACE,
    session_id_for,
    session_key,
)

LOCATION = uuid.UUID("62655708-0330-475f-aa28-c4749ded4b9d")
WORKOUT_TIME = datetime.datetime(2026, 8, 20, 21, 20, tzinfo=datetime.timezone.utc)


class TestSessionKey:
    """Test the string a session's id is derived from."""

    def test_the_key_pairs_the_location_with_the_time(self):
        assert session_key(LOCATION, WORKOUT_TIME) == f"{LOCATION}|2026-08-20T21:20:00Z"

    def test_an_offset_time_is_normalised_to_utc(self):
        """The same instant must give the same key however it is expressed."""
        bst = datetime.datetime(
            2026,
            8,
            20,
            22,
            20,
            tzinfo=datetime.timezone(datetime.timedelta(hours=1)),
        )

        assert session_key(LOCATION, bst) == session_key(LOCATION, WORKOUT_TIME)

    def test_a_naive_time_is_read_as_utc(self):
        naive = datetime.datetime(2026, 8, 20, 21, 20)

        assert session_key(LOCATION, naive) == session_key(LOCATION, WORKOUT_TIME)

    def test_microseconds_are_dropped(self):
        """A stray microsecond must not split one session into two."""
        precise = WORKOUT_TIME.replace(microsecond=123456)

        assert session_key(LOCATION, precise) == session_key(LOCATION, WORKOUT_TIME)


class TestSessionIdFor:
    """Test the derived session id.

    Re-running the sheet load must merge onto the same rows, so these ids are
    a contract: changing how they are derived orphans every existing session.
    """

    def test_the_id_is_stable(self):
        assert session_id_for(LOCATION, WORKOUT_TIME) == uuid.UUID(
            "6cd3905a-3bfa-53ca-a9e4-331557a3c04c"
        )

    def test_the_same_session_gives_the_same_id(self):
        assert session_id_for(LOCATION, WORKOUT_TIME) == session_id_for(
            LOCATION, WORKOUT_TIME
        )

    def test_a_different_time_gives_a_different_id(self):
        other = WORKOUT_TIME + datetime.timedelta(minutes=1)

        assert session_id_for(LOCATION, other) != session_id_for(LOCATION, WORKOUT_TIME)

    def test_a_different_location_gives_a_different_id(self):
        other = uuid.UUID("97cffa7f-6b99-47a0-9a3f-adbbb7409dea")

        assert session_id_for(other, WORKOUT_TIME) != session_id_for(
            LOCATION, WORKOUT_TIME
        )

    def test_the_id_is_a_uuid5(self):
        assert session_id_for(LOCATION, WORKOUT_TIME).version == 5

    @pytest.mark.parametrize(
        "namespace", [uuid.NAMESPACE_DNS, uuid.NAMESPACE_URL, uuid.uuid4()]
    )
    def test_the_namespace_is_not_a_standard_one(self, namespace: uuid.UUID):
        assert SESSION_NAMESPACE != namespace
