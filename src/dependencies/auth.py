from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.common import decode_token
from src.db import session
from src.models.user import Role, User

_bearer = HTTPBearer()


def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> User:
    try:
        print(credentials.credentials)
        claims = decode_token(credentials.credentials)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user: Optional[User] = (
        session.query(User).filter(User.google_account_id == claims["sub"]).first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


_ROLE_HIERARCHY: dict[Role, int] = {
    Role.none: 0,
    Role.viewer: 1,
    Role.editor: 2,
    Role.admin: 3,
}


def require_role(minimum_role: Role):
    def dependency(user: User = Depends(_get_current_user)) -> User:
        if _ROLE_HIERARCHY[user.role] < _ROLE_HIERARCHY[minimum_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires '{minimum_role.value}' role or above",
            )
        return user

    return dependency
