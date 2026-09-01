import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["default"])


@router.post("/sleep")
async def inspect_sleep_payload(request: Request) -> Dict[str, Any]:
    """Temporary inspection endpoint for the Health/Shortcuts export while
    its payload shape is still being figured out. No auth, and does not
    write anything - just logs whatever is posted (visible in the server
    log) and echoes it back, so a real payload can be pasted for review
    before building the actual session-enrichment mapping.
    """
    body = await request.body()
    try:
        payload: Any = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = body.decode("utf-8", errors="replace")

    logger.info(f"POST /health/sleep received: {payload}")
    return {"received": payload}
