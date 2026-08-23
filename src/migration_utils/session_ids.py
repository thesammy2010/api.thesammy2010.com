"""Deterministic identity for a workout session.

The sheet has no session id, so one is derived from the location and the time.
The alembic backfill and the sheet loader both use this, and they must agree:
a random id would make every re-run of the load insert a duplicate session
rather than merging onto the existing one.

Kept free of any database or config import so that it stays unit testable.
"""

import datetime
import uuid

# uuid5(NAMESPACE_DNS, "go-heavier.thesammy2010.com/sessions"), written out so
# that it can never drift with a change to how it was derived.
SESSION_NAMESPACE = uuid.UUID("f6c5586a-21de-56bb-94ca-69b75e100a62")


def session_key(location_id: uuid.UUID, workout_time: datetime.datetime) -> str:
    """The string a session's id is derived from.

    The time is normalised to UTC and truncated to the second so that the same
    session cannot produce two keys through a differing offset or a stray
    microsecond.
    """
    if workout_time.tzinfo is None:
        workout_time = workout_time.replace(tzinfo=datetime.timezone.utc)
    utc = workout_time.astimezone(datetime.timezone.utc)

    return f"{location_id}|{utc.strftime('%Y-%m-%dT%H:%M:%S')}Z"


def session_id_for(
    location_id: uuid.UUID, workout_time: datetime.datetime
) -> uuid.UUID:
    """The id of the session at this location and time, the same on every run."""
    return uuid.uuid5(SESSION_NAMESPACE, session_key(location_id, workout_time))
