from typing import Annotated, Dict

from fastapi import APIRouter, Header, HTTPException

from src.common import CommonHeaders, decode_token
from src.resolvers.squash.users import create_user_in_db, get_current_user

router = APIRouter(prefix="/squash", tags=["squash"])


@router.get("/users")
async def get_user(headers: Annotated[CommonHeaders, Header()]) -> Dict[str, str]:
    user = get_current_user(headers.authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": str(
            get_current_user(headers.authorization.replace("Bearer ", "")).id
        )
    }


@router.post("/users")
async def create_user(headers: Annotated[CommonHeaders, Header()]) -> Dict[str, str]:
    try:
        claims = decode_token(headers.authorization.replace("Bearer ", ""))
    except Exception:
        raise HTTPException(
            status_code=401, detail="User must be authenticated with Google"
        )
    return {"user_id": str(create_user_in_db(claims).id)}
