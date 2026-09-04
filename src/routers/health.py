import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

import pendulum
from fastapi import APIRouter, Request

from src.db import session
from src.models.go_heavier import SleepRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["default"])

# Shortcuts' own text summary of a Sleep Analysis sample, e.g.:
#   1 Sep 2026 at 01:45-1 Sep 2026 at 09:06
#   Total Time Asleep:7.22 hours
#
#   Awake for 1 hours and 17 minutes
#   Core for 2 hours and 47 minutes
#   Deep for 0 hours and 58 minutes
#   REM for 2 hours and 11 minutes
_DATETIME_FORMAT = "%d %b %Y at %H:%M"
_RANGE_RE = re.compile(
    r"(\d{1,2} \w{3} \d{4} at \d{2}:\d{2})-(\d{1,2} \w{3} \d{4} at \d{2}:\d{2})"
)
_TOTAL_ASLEEP_RE = re.compile(r"Total Time Asleep:\s*([\d.]+)\s*hours")
_STAGE_RE = re.compile(r"(\w+) for (\d+) hours? and (\d+) minutes?")


def _parse_local_datetime(value: str) -> Optional[pendulum.DateTime]:
    """Shortcuts gives no timezone, so this is read as UK local time, the
    same assumption the sheet load makes for workout_time."""
    try:
        naive = datetime.strptime(value, _DATETIME_FORMAT)
    except ValueError:
        return None
    return pendulum.instance(naive, tz="Europe/London").in_tz("UTC")


def parse_sleep_summary(text: str) -> Dict[str, Any]:
    """Parses the free-text sleep summary a Shortcuts automation sends.

    Every field is optional in the output - a summary missing a stage (no
    REM recorded, say) or the total-asleep line still parses as far as it
    can rather than failing outright.
    """
    bed_time = wake_time = None
    range_match = _RANGE_RE.search(text)
    if range_match:
        bed_time = _parse_local_datetime(range_match.group(1))
        wake_time = _parse_local_datetime(range_match.group(2))

    sleep_hours = None
    total_match = _TOTAL_ASLEEP_RE.search(text)
    if total_match:
        sleep_hours = float(total_match.group(1))

    stages_minutes = {
        stage: int(hours) * 60 + int(minutes)
        for stage, hours, minutes in _STAGE_RE.findall(text)
    }

    return {
        "bed_time": bed_time,
        "wake_time": wake_time,
        "sleep_hours": sleep_hours,
        "stages_minutes": stages_minutes,
    }


@router.post("/sleep")
async def receive_sleep_export(request: Request) -> Dict[str, Any]:
    """Receives a Shortcuts sleep export, parses it, and stores it.

    Deliberately unauthenticated for now, since a Shortcut can't easily
    carry a Google token - not meant to be exposed on production as-is.
    A session is never looked up or written here: matching a stored
    record onto a session happens the other way around, when
    POST /go-heavier/sessions creates one (see
    resolvers.go_heavier.sessions.create_session), since sleep data
    normally arrives well before that day's session exists.
    """
    body = await request.body()
    try:
        payload: Any = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = body.decode("utf-8", errors="replace")

    parsed = None
    record_id = None
    if isinstance(payload, dict) and isinstance(payload.get("sleep"), str):
        parsed = parse_sleep_summary(payload["sleep"])
        if parsed["wake_time"] is not None:
            record = SleepRecord(
                bed_time=parsed["bed_time"],
                wake_time=parsed["wake_time"],
                sleep_hours=parsed["sleep_hours"],
                stages_minutes=parsed["stages_minutes"] or None,
            )
            session.add(record)
            session.commit()
            record_id = record.id

    logger.warning(f"POST /health/sleep received: {payload}")
    if parsed is not None:
        logger.warning(f"POST /health/sleep parsed: {parsed} stored_as={record_id}")

    return {"received": payload, "parsed": parsed, "stored_as": record_id}
