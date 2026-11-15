import datetime
import uuid
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import ForeignKey

from src.models import Base


class Player(Base):
    """Someone who plays in the squash group.

    Being a player, rather than a role, is what lets a user into /squash, so
    friends can play without being able to read Go Heavier too. A player
    without a user is someone who's been recorded in a match but has never
    signed in. Given an email, they're linked to their user the first time
    that user calls /squash.
    """

    __tablename__ = "squash_players"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True, unique=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Stored lowercased, to match a user's Google email against
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )
    # Left out of the group without losing their matches
    is_active: Mapped[bool] = mapped_column(
        Boolean(), nullable=False, server_default="true"
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

    def __repr__(self) -> str:
        return f"<Player(id={self.id}, name={self.name})>"
