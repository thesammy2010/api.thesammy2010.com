import dataclasses
import uuid
from typing import Annotated, List, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import func

from src.common import UserRole
from src.db import session
from src.models.squash import Player as DBPlayer
from src.models.user import User
from src.resolvers.users import require_squash
from src.schemas.squash.players import PlayerRequest


class NotFound(LookupError):
    """Raised when a request refers to a row that doesn't exist."""


class NotAllowed(PermissionError):
    """Raised when the caller can't change what they asked to."""


class Conflict(ValueError):
    """Raised when a change would clash with what's already there."""


@dataclasses.dataclass
class SquashCaller:
    user: User
    # None for an admin who doesn't play
    player: Optional[DBPlayer]

    @property
    def is_admin(self) -> bool:
        return self.user.role == UserRole.ADMIN.value


def require_squash_player(
    user: Annotated[User, Depends(require_squash)],
) -> SquashCaller:
    """Lets in a user with the squash role or above who's an active player,
    or any admin.

    Anyone with a Google account becomes a guest by signing in, so it takes
    an admin both giving a friend the squash role, which opens nothing else,
    and adding them as a player, linked to their user or by their email. An
    email is linked here the first time they call once they have the role.
    """
    player = (
        session.query(DBPlayer).filter(DBPlayer.user_id == user.id).one_or_none()
    ) or _claim_by_email(user)
    if player is not None and not player.is_active:
        player = None
    caller = SquashCaller(user=user, player=player)
    if player is None and not caller.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: you aren't a player in the squash group",
        )
    return caller


def _claim_by_email(user: User) -> Optional[DBPlayer]:
    """Links the user to the unlinked player added with their email."""
    if not user.email:
        return None
    player = (
        session.query(DBPlayer)
        .filter(DBPlayer.user_id.is_(None), DBPlayer.email == user.email.lower())
        .one_or_none()
    )
    if player is not None:
        player.user_id = user.id
        session.commit()
    return player


def require_squash_admin(
    caller: Annotated[SquashCaller, Depends(require_squash_player)],
) -> SquashCaller:
    if not caller.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only an admin can manage players",
        )
    return caller


def get_players(include_inactive: bool) -> List[DBPlayer]:
    query = session.query(DBPlayer)
    if not include_inactive:
        query = query.filter(DBPlayer.is_active.is_(True))
    return query.order_by(DBPlayer.name, DBPlayer.id).all()


def get_player(player_id: uuid.UUID) -> Optional[DBPlayer]:
    return session.get(DBPlayer, player_id)


def _fields(player: PlayerRequest, player_id: Optional[uuid.UUID]) -> dict:
    """The request's fields as the model stores them, linking the user with
    the player's email when no user is given and one has signed in with it."""
    fields = player.model_dump()
    if fields["user_id"] is None and player.email:
        user = (
            session.query(User)
            .filter(func.lower(User.email) == player.email, User.deleted_at.is_(None))
            .first()
        )
        if user is not None:
            fields["user_id"] = user.id

    user_id = fields["user_id"]
    if user_id is not None:
        user = session.get(User, user_id)
        if user is None or user.deleted_at is not None:
            raise NotFound(f"User {user_id} not found")
        linked = (
            session.query(DBPlayer).filter(DBPlayer.user_id == user_id).one_or_none()
        )
        if linked is not None and linked.id != player_id:
            raise Conflict(f"User {user_id} is already player {linked.id}")
    if player.email:
        taken = (
            session.query(DBPlayer).filter(DBPlayer.email == player.email).one_or_none()
        )
        if taken is not None and taken.id != player_id:
            raise Conflict(f"{player.email} is already player {taken.id}")
    return fields


def create_player(player: PlayerRequest) -> DBPlayer:
    new_player = DBPlayer(id=uuid.uuid4(), **_fields(player, None))
    session.add(new_player)
    session.commit()
    return new_player


def update_player(player_id: uuid.UUID, player: PlayerRequest) -> Optional[DBPlayer]:
    db_player = get_player(player_id)
    if not db_player:
        return None
    for field, value in _fields(player, player_id).items():
        setattr(db_player, field, value)
    session.commit()
    return db_player
