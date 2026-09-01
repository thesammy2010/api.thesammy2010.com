import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

import pendulum
from fastapi import APIRouter, Request

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
async def inspect_sleep_payload(request: Request) -> Dict[str, Any]:
    """Temporary inspection endpoint for the Shortcuts sleep export while
    its payload shape is still being figured out. No auth, and does not
    write anything - logs and echoes back both the raw payload and, if it
    has a "sleep" text field, the parsed result, so the parsing can be
    checked against a real export before it's wired into session
    enrichment.
    """
    body = await request.body()
    try:
        payload: Any = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = body.decode("utf-8", errors="replace")

    parsed = None
    if isinstance(payload, dict) and isinstance(payload.get("sleep"), str):
        parsed = parse_sleep_summary(payload["sleep"])

    logger.warning(f"POST /health/sleep received: {payload}")
    if parsed is not None:
        logger.warning(f"POST /health/sleep parsed: {parsed}")

    return {"received": payload, "parsed": parsed}
