import logging
import uuid
from typing import Annotated, Any, Callable, Dict, List, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, or_

from src.common import ROLE_RANK, UserRole, require_auth
from src.config import Config
from src.db import session
from src.models.user import User, UserAuditLog
from src.schemas.users import ListUsersRequest

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
    """Get-or-create by google_account_id, refreshing email/name and
    stamping last_signed_in_at either way - this is the choke point every
    authenticated request passes through (directly for POST /users, or via
    provision_current_user for everything else), so it doubles as "last
    seen with a valid token".

    A first-time sign-in whose email matches an admin-provisioned,
    not-yet-claimed placeholder (google_account_id still NULL) claims that
    row instead of creating a new GUEST one, so the role the admin set for
    them takes effect immediately.
    """
    sub = claims["sub"]
    email = claims.get("email")
    name = claims.get("name")

    existing_user = (
        session.query(User)
        .where(User.google_account_id == sub, User.deleted_at.is_(None))
        .first()
    )
    if existing_user:
        existing_user.email = email
        existing_user.name = name
        existing_user.last_signed_in_at = func.now()
        session.commit()
        return existing_user

    placeholder = (
        session.query(User)
        .where(
            User.google_account_id.is_(None),
            User.email == email,
            User.deleted_at.is_(None),
        )
        .first()
        if email
        else None
    )
    if placeholder:
        placeholder.google_account_id = sub
        placeholder.name = name
        placeholder.last_signed_in_at = func.now()
        _log_audit(
            actor_id=placeholder.id, target_user_id=placeholder.id, action="claimed"
        )
        session.commit()
        return placeholder

    user = User(
        google_account_id=sub, email=email, name=name, last_signed_in_at=func.now()
    )
    session.add(user)
    session.flush()
    _log_audit(actor_id=user.id, target_user_id=user.id, action="created")
    session.commit()
    return user


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


def list_users(request: ListUsersRequest) -> List[User]:
    return (
        session.query(User)
        .where(User.deleted_at.is_(None))
        .order_by(User.created_at)
        .limit(Config.DEFAULT_DB_PAGE_SIZE)
        .offset(request.offset)
        .all()
    )


def create_user_admin(
    actor: User,
    role: UserRole,
    google_account_id: Optional[str] = None,
    email: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[User]:
    """Pre-provisions a user by google_account_id, email, or both.

    Email is the identifier an admin actually has - they invite someone by
    email, not by an opaque Google account id - so an email-only row is
    left with google_account_id NULL and claimed automatically the first
    time that person signs in (see create_user_in_db), at which point their
    real email/name overwrite whatever was given here. Returns None if an
    active user already exists for either identifier given.
    """
    conditions = [
        condition
        for condition, value in (
            (User.google_account_id == google_account_id, google_account_id),
            (User.email == email, email),
        )
        if value
    ]
    existing_user = (
        session.query(User).where(User.deleted_at.is_(None), or_(*conditions)).first()
    )
    if existing_user:
        return None
    user = User(
        google_account_id=google_account_id, role=role.value, email=email, name=name
    )
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
