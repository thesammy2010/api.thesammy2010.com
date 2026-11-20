"""Asking to join the squash group, and an admin's answer.

Signing in only makes someone a guest, so this is how a friend who hasn't
been added yet lets an admin know, rather than asking them some other way.
"""

import datetime
import uuid
from typing import List, Optional

from sqlalchemy import delete

from src.db import session
from src.models.squash import AccessRequest as DBAccessRequest
from src.models.squash import Player as DBPlayer
from src.models.user import User
from src.resolvers.squash.players import Conflict, NotFound
from src.schemas.squash.access_requests import (
    AccessRequestRequest,
    ApproveAccessRequestRequest,
    ListAccessRequestsRequest,
)
from src.schemas.squash.enums import AccessRequestStatus

PENDING = AccessRequestStatus.PENDING.value


def _active_player(user: User) -> Optional[DBPlayer]:
    """The player the user is, or will be linked to by their email the next
    time they use /squash, if they're still in the group."""
    player = session.query(DBPlayer).filter(DBPlayer.user_id == user.id).one_or_none()
    if player is None and user.email:
        player = (
            session.query(DBPlayer)
            .filter(DBPlayer.user_id.is_(None), DBPlayer.email == user.email.lower())
            .one_or_none()
        )
    return player if player is not None and player.is_active else None


def get_own_request(user: User) -> Optional[DBAccessRequest]:
    """The user's latest request, whatever became of it."""
    return (
        session.query(DBAccessRequest)
        .filter(DBAccessRequest.user_id == user.id)
        .order_by(DBAccessRequest.created_at.desc())
        .first()
    )


def create_request(user: User, request: AccessRequestRequest) -> DBAccessRequest:
    if _active_player(user) is not None:
        raise Conflict("You're already in the squash group")
    pending = (
        session.query(DBAccessRequest)
        .filter(DBAccessRequest.user_id == user.id, DBAccessRequest.status == PENDING)
        .one_or_none()
    )
    if pending is not None:
        raise Conflict("You've already asked, and it's waiting for an admin")
    access_request = DBAccessRequest(
        id=uuid.uuid4(), user_id=user.id, message=request.message, status=PENDING
    )
    session.add(access_request)
    session.commit()
    return access_request


def withdraw_requests(user: User) -> bool:
    """Deletes the user's pending and declined requests, so a declined one
    no longer shows either. An approved one is kept as the record of how
    they joined. False if there were none."""
    deleted = session.execute(
        delete(DBAccessRequest).where(
            DBAccessRequest.user_id == user.id,
            DBAccessRequest.status != AccessRequestStatus.APPROVED.value,
        )
    ).rowcount
    session.commit()
    return deleted > 0


def get_requests(request: ListAccessRequestsRequest) -> List[DBAccessRequest]:
    """Requests from users who still have an account, newest first."""
    query = (
        session.query(DBAccessRequest)
        .join(User, User.id == DBAccessRequest.user_id)
        .filter(User.deleted_at.is_(None))
    )
    if request.status:
        query = query.filter(DBAccessRequest.status == request.status.value)
    return query.order_by(DBAccessRequest.created_at.desc()).all()


def _pending_request(request_id: uuid.UUID) -> DBAccessRequest:
    access_request = session.get(DBAccessRequest, request_id)
    if access_request is None or access_request.user.deleted_at is not None:
        raise NotFound("Access request not found")
    if access_request.status != PENDING:
        raise Conflict(f"The request has already been {access_request.status}")
    return access_request


def _player_for(user: User, approval: ApproveAccessRequestRequest) -> DBPlayer:
    """The player the user becomes: the one asked for, the one they already
    were, the one added with their email, or else a new one."""
    linked = session.query(DBPlayer).filter(DBPlayer.user_id == user.id).one_or_none()
    if approval.player_id is not None:
        player = session.get(DBPlayer, approval.player_id)
        if player is None:
            raise NotFound(f"Player {approval.player_id} not found")
        if linked is not None and linked.id != player.id:
            raise Conflict(f"They're already player {linked.id}")
        if player.user_id is not None and player.user_id != user.id:
            raise Conflict(f"Player {player.id} is already someone else")
        player.user_id = user.id
        return player
    if linked is not None:
        return linked

    email = user.email.lower() if user.email else None
    if email:
        by_email = session.query(DBPlayer).filter(DBPlayer.email == email).one_or_none()
        if by_email is not None and by_email.user_id is None:
            by_email.user_id = user.id
            return by_email
        if by_email is not None:
            # Taken by someone else's player, so the new one goes without
            email = None
    player = DBPlayer(
        id=uuid.uuid4(),
        name=approval.name or user.name or user.email or "New player",
        email=email,
        user_id=user.id,
    )
    session.add(player)
    return player


def _reviewed(access_request: DBAccessRequest, reviewer: User, status: str) -> None:
    access_request.status = status
    access_request.reviewed_by_id = reviewer.id
    access_request.reviewed_at = datetime.datetime.now()


def approve_request(
    request_id: uuid.UUID, reviewer: User, approval: ApproveAccessRequestRequest
) -> DBAccessRequest:
    """Lets the user in as a player, back in the group if they'd left it."""
    access_request = _pending_request(request_id)
    player = _player_for(access_request.user, approval)
    player.is_active = True
    access_request.player_id = player.id
    _reviewed(access_request, reviewer, AccessRequestStatus.APPROVED.value)
    session.commit()
    return access_request


def decline_request(request_id: uuid.UUID, reviewer: User) -> DBAccessRequest:
    access_request = _pending_request(request_id)
    _reviewed(access_request, reviewer, AccessRequestStatus.DECLINED.value)
    session.commit()
    return access_request
