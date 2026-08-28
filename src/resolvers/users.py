import logging
import uuid
from typing import Annotated, Any, Callable, Dict, Optional

from fastapi import Depends, HTTPException, status

from src.common import ROLE_RANK, UserRole, require_auth
from src.db import session
from src.models.user import User

logger = logging.getLogger(__name__)


def find_user_by_claims(claims: Dict[str, str]) -> Optional[User]:
    return session.query(User).where(User.google_account_id == claims["sub"]).first()


def create_user_in_db(claims: Dict[str, str]) -> User:
    existing_user = (
        session.query(User).where(User.google_account_id == claims["sub"]).first()
    )
    if not existing_user:
        user = User(google_account_id=claims["sub"])
        session.add(user)
        session.commit()
        return user
    return existing_user


def provision_current_user(
    claims: Annotated[Dict[str, Any], Depends(require_auth)],
) -> User:
    """Ensures every authenticated caller has a row in `users`.

    Used as the auth dependency on every protected route, so a user is
    recorded the first time they call the API with a valid token - no
    separate sign-up step needed for them to show up and be manageable.
    """
    return create_user_in_db(claims)


def require_role(minimum: UserRole) -> Callable[..., User]:
    """Builds a dependency that gates a route behind a minimum role.

    A new user defaults to GUEST, so this also doubles as the auth gate:
    a route behind require_role(UserRole.VIEWER) or higher is unreachable
    until an admin promotes the caller past GUEST.
    """

    def dependency(user: Annotated[User, Depends(provision_current_user)]) -> User:
        if ROLE_RANK[UserRole(user.role)] < ROLE_RANK[minimum]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Permission denied: this action requires the {minimum.value} "
                    f"role or higher, but your role is {user.role}"
                ),
            )
        return user

    return dependency


require_viewer = require_role(UserRole.VIEWER)
require_editor = require_role(UserRole.EDITOR)
require_admin = require_role(UserRole.ADMIN)


def set_user_role(user_id: uuid.UUID, role: UserRole) -> Optional[User]:
    user = session.get(User, user_id)
    if not user:
        return None
    user.role = role.value
    session.commit()
    return user
