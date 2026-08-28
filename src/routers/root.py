import logging
import uuid
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.routing import APIRoute

from src.common import UserRole, require_auth
from src.models.user import User
from src.resolvers.users import (
    create_user_admin,
    create_user_in_db,
    delete_user_admin,
    find_user_by_claims,
    list_users,
    require_admin,
    require_editor,
    require_viewer,
    set_user_role,
)
from src.schemas.users import (
    CreateUserRequest,
    ListUsersRequest,
    UpdateUserRoleRequest,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


@router.get("/users", response_model=UserResponse)
async def get_user(claims: Annotated[Dict[str, Any], Depends(require_auth)]) -> User:
    """The caller's own user record. 404 if they haven't signed up yet."""
    user = find_user_by_claims(claims)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users", response_model=UserResponse)
async def create_user(claims: Annotated[Dict[str, Any], Depends(require_auth)]) -> User:
    """Registers the caller, or returns their existing record if already
    registered. New accounts start as GUEST; an admin must promote them."""
    return create_user_in_db(claims)


def _required_role(route: APIRoute) -> Optional[UserRole]:
    """Walks a route's dependency tree to find its role gate, if any.

    require_viewer/editor/admin are each one specific function object (see
    require_role in resolvers/users.py), so identity comparison against the
    collected dependency callables tells us exactly which gate, if any, a
    route sits behind - without maintaining a second, separate list that
    could drift from what's actually enforced.
    """
    calls = set()

    def collect(dependant) -> None:
        if dependant.call is not None:
            calls.add(dependant.call)
        for sub_dependant in dependant.dependencies:
            collect(sub_dependant)

    collect(route.dependant)

    if require_admin in calls:
        return UserRole.ADMIN
    if require_editor in calls:
        return UserRole.EDITOR
    if require_viewer in calls:
        return UserRole.VIEWER
    if require_auth in calls:
        return UserRole.GUEST
    return None


@router.get("/endpoints", dependencies=[Depends(require_auth)])
def get_endpoint_roles(request: Request) -> Dict[str, Dict[str, Optional[UserRole]]]:
    """Every endpoint and the minimum role it requires, keyed by path then
    HTTP method. A null role means the endpoint needs no auth at all.

    Needs only a valid token, not any particular role, since even a GUEST
    should be able to see what they'll unlock once promoted.
    """
    endpoints: Dict[str, Dict[str, Optional[UserRole]]] = {}
    for route in request.app.routes:
        if not isinstance(route, APIRoute):
            continue
        role = _required_role(route)
        for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
            endpoints.setdefault(route.path, {})[method] = role
    return endpoints


@router.get("/admin/users", response_model=List[UserResponse])
async def admin_list_users(
    actor: Annotated[User, Depends(require_admin)],
    request: Annotated[ListUsersRequest, Query()],
) -> List[User]:
    """Lists every user, oldest first, deleted included. Admin-only."""
    return list_users(request)


@router.post("/admin/users", response_model=UserResponse)
async def admin_create_user(
    actor: Annotated[User, Depends(require_admin)], request: CreateUserRequest
) -> UserResponse:
    """Pre-provisions a Google account with a starting role, before that
    person has ever signed in. Admin-only. 409 if an active user for that
    account already exists."""
    user = create_user_admin(
        actor=actor, google_account_id=request.google_account_id, role=request.role
    )
    if not user:
        raise HTTPException(status_code=409, detail="User already exists")
    return user


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    actor: Annotated[User, Depends(require_admin)],
    user_id: uuid.UUID,
    request: UpdateUserRoleRequest,
) -> UserResponse:
    """Sets a user's role. Admin-only, including for an admin's own role."""
    user = set_user_role(actor=actor, user_id=user_id, role=request.role)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/users/{user_id}", response_model=UserResponse)
async def delete_user(
    actor: Annotated[User, Depends(require_admin)], user_id: uuid.UUID
) -> UserResponse:
    """Soft-deletes a user: marks them deleted rather than removing the
    row, so their audit trail and anything they created stay intact.
    Admin-only. Their google_account_id becomes available for a fresh
    sign-up. 404 if they don't exist or are already deleted."""
    user = delete_user_admin(actor=actor, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
