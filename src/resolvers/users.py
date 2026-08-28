import logging
import uuid
from typing import Annotated, Any, Callable, Dict, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import func

from src.common import ROLE_RANK, UserRole, require_auth
from src.db import session
from src.models.user import User, UserAuditLog

logger = logging.getLogger(__name__)


def _log_audit(
    actor_id: uuid.UUID,
    target_user_id: uuid.UUID,
    action: str,
    previous_role: Optional[str] = None,
    new_role: Optional[str] = None,
) -> None:
    session.add(
        UserAuditLog(
            actor_id=actor_id,
            target_user_id=target_user_id,
            action=action,
            previous_role=previous_role,
            new_role=new_role,
        )
    )


def find_user_by_claims(claims: Dict[str, str]) -> Optional[User]:
    return (
        session.query(User)
        .where(User.google_account_id == claims["sub"], User.deleted_at.is_(None))
        .first()
    )


def create_user_in_db(claims: Dict[str, str]) -> User:
    existing_user = (
        session.query(User)
        .where(User.google_account_id == claims["sub"], User.deleted_at.is_(None))
        .first()
    )
    if not existing_user:
        user = User(google_account_id=claims["sub"])
        session.add(user)
        session.flush()
        _log_audit(actor_id=user.id, target_user_id=user.id, action="created")
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


def set_user_role(actor: User, user_id: uuid.UUID, role: UserRole) -> Optional[User]:
    user = session.get(User, user_id)
    if not user or user.deleted_at is not None:
        return None
    previous_role = user.role
    user.role = role.value
    _log_audit(
        actor_id=actor.id,
        target_user_id=user.id,
        action="role_changed",
        previous_role=previous_role,
        new_role=role.value,
    )
    session.commit()
    return user


def create_user_admin(
    actor: User, google_account_id: str, role: UserRole
) -> Optional[User]:
    """Pre-provisions a specific Google account with a starting role.

    Lets an admin invite someone before they've ever signed in, so their
    first request lands on an already-configured row instead of GUEST.
    Returns None if an active user for that account already exists.
    """
    existing_user = (
        session.query(User)
        .where(User.google_account_id == google_account_id, User.deleted_at.is_(None))
        .first()
    )
    if existing_user:
        return None
    user = User(google_account_id=google_account_id, role=role.value)
    session.add(user)
    session.flush()
    _log_audit(
        actor_id=actor.id, target_user_id=user.id, action="created", new_role=role.value
    )
    session.commit()
    return user


def delete_user_admin(actor: User, user_id: uuid.UUID) -> Optional[User]:
    """Soft-deletes a user: marks them deleted rather than removing the row,
    so their audit trail and anything they created stay intact."""
    user = session.get(User, user_id)
    if not user or user.deleted_at is not None:
        return None
    user.deleted_at = func.now()
    _log_audit(actor_id=actor.id, target_user_id=user.id, action="deleted")
    session.commit()
    return user
