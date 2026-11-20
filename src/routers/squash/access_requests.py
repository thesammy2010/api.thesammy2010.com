import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from src.models.squash import AccessRequest as DBAccessRequest
from src.models.user import User
from src.resolvers.squash import access_requests
from src.resolvers.squash.players import (
    Conflict,
    NotFound,
    SquashCaller,
    require_squash_admin,
)
from src.resolvers.users import provision_current_user
from src.routers.squash import parse_uuid
from src.schemas.squash.access_requests import (
    AccessRequestRequest,
    AccessRequestResponse,
    AdminAccessRequestResponse,
    ApproveAccessRequestRequest,
    ListAccessRequestsRequest,
)

# Unlike the rest of /squash, the caller's own request is for anyone signed
# in, since it's how someone who isn't a player yet asks to become one.
# Reviewing them is admin-only, set on each route.
router = APIRouter(prefix="/squash", tags=["squash access requests"])


@router.get("/access-requests/me", response_model=AccessRequestResponse)
def get_own_request(
    user: Annotated[User, Depends(provision_current_user)],
) -> DBAccessRequest:
    """The caller's latest request to join the group. 404 if they haven't
    made one, or withdrew it."""
    access_request = access_requests.get_own_request(user)
    if access_request is None:
        raise HTTPException(status_code=404, detail="You haven't asked to join")
    return access_request


@router.post("/access-requests/me", response_model=AccessRequestResponse)
def create_request(
    user: Annotated[User, Depends(provision_current_user)],
    request: AccessRequestRequest,
) -> DBAccessRequest:
    """Asks an admin to let the caller into the group. 409 if they're
    already in it, or already have a request waiting."""
    try:
        return access_requests.create_request(user, request)
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/access-requests/me", status_code=204)
def withdraw_requests(
    user: Annotated[User, Depends(provision_current_user)],
) -> Response:
    """Withdraws the caller's request, or clears one that was declined, so
    they can ask again. 404 if there's nothing to withdraw."""
    if not access_requests.withdraw_requests(user):
        raise HTTPException(status_code=404, detail="You haven't asked to join")
    return Response(status_code=204)


@router.get(
    "/access-requests",
    response_model=List[AdminAccessRequestResponse],
    dependencies=[Depends(require_squash_admin)],
)
def get_requests(
    request: Annotated[ListAccessRequestsRequest, Query()],
) -> List[AdminAccessRequestResponse]:
    """Requests to join, newest first, with who made them. Admin-only."""
    return [
        AdminAccessRequestResponse.of(access_request)
        for access_request in access_requests.get_requests(request)
    ]


@router.post(
    "/access-requests/{request_id}/approve",
    response_model=AdminAccessRequestResponse,
)
def approve_request(
    caller: Annotated[SquashCaller, Depends(require_squash_admin)],
    request_id: Annotated[str, uuid.UUID],
    approval: ApproveAccessRequestRequest,
) -> AdminAccessRequestResponse:
    """Makes the requester a player, so they can use /squash. Admin-only.

    They become the player given, such as someone already recorded in
    matches, else the one they were before or the one added with their
    email, else a new player. 404 if the request or player doesn't exist,
    409 if it's already been reviewed or the player is someone else.
    """
    try:
        return AdminAccessRequestResponse.of(
            access_requests.approve_request(
                parse_uuid(request_id, "access request"), caller.user, approval
            )
        )
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post(
    "/access-requests/{request_id}/decline",
    response_model=AdminAccessRequestResponse,
)
def decline_request(
    caller: Annotated[SquashCaller, Depends(require_squash_admin)],
    request_id: Annotated[str, uuid.UUID],
) -> AdminAccessRequestResponse:
    """Turns a request down. They can withdraw it and ask again. Admin-only.
    409 if it's already been reviewed."""
    try:
        return AdminAccessRequestResponse.of(
            access_requests.decline_request(
                parse_uuid(request_id, "access request"), caller.user
            )
        )
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e))
