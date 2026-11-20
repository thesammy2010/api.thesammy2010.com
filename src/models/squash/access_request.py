import datetime
import uuid
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import ForeignKey

from src.models import Base
from src.models.user import User


class AccessRequest(Base):
    """Someone who's signed in asking to be let into the squash group.

    An admin approves it, making them a player, or declines it. Only one can
    be pending for a user at a time, but they can ask again once it's been
    looked at, or withdraw it first.
    """

    __tablename__ = "squash_access_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'declined')", name="status_is_known"
        ),
        Index(
            "uq_squash_access_requests_pending_user_id",
            "user_id",
            unique=True,
            postgresql_where="status = 'pending'",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    # Anything they'd like the admin to know, such as who they play with
    message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # One of AccessRequestStatus, stored as its value
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="pending"
    )
    # The player they became, once approved
    player_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("squash_players.id"), nullable=True
    )
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(), nullable=True
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.datetime.now
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(),
        nullable=True,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    )

    user: Mapped[User] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<AccessRequest(id={self.id}, status={self.status})>"
