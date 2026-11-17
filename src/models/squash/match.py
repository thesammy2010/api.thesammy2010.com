import datetime
import uuid
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import ForeignKey

from src.models import Base


class Match(Base):
    """A singles or doubles match, from being arranged to its result.

    The two sides are numbered 1 and 2, and a match's players and games
    refer to them by that number.
    """

    __tablename__ = "squash_matches"
    __table_args__ = (
        CheckConstraint("points_to > 0", name="points_to_positive"),
        CheckConstraint("best_of IS NULL OR mod(best_of, 2) = 1", name="best_of_odd"),
        CheckConstraint("winning_side IN (1, 2)", name="winning_side_is_a_side"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    # One of MatchFormat, stored as its value
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    # One of MatchStatus, stored as its value
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    # When it's arranged for, or was played
    played_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    venue_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("squash_venues.id"), nullable=True, index=True
    )
    points_to: Mapped[int] = mapped_column(
        SmallInteger(), nullable=False, server_default="11"
    )
    # Null when games are just played until people stop
    best_of: Mapped[Optional[int]] = mapped_column(SmallInteger(), nullable=True)
    # Set once the match is completed, so results can be counted without
    # replaying every game
    winning_side: Mapped[Optional[int]] = mapped_column(SmallInteger(), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    # Goes up by one on every change, so a phone can tell whether what it's
    # showing is current, and a point scored from a stale score is turned away
    version: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="1")

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
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

    players: Mapped[List["MatchPlayer"]] = relationship(
        cascade="all, delete-orphan",
        order_by="(MatchPlayer.side, MatchPlayer.player_id)",
    )
    games: Mapped[List["Game"]] = relationship(
        cascade="all, delete-orphan", order_by="Game.number"
    )
    venue: Mapped[Optional["Venue"]] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<Match(id={self.id}, format={self.format}, status={self.status})>"


class MatchPlayer(Base):
    """Who played on which side of a match."""

    __tablename__ = "squash_match_players"
    __table_args__ = (CheckConstraint("side IN (1, 2)", name="side_is_a_side"),)

    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("squash_matches.id", ondelete="CASCADE"), primary_key=True
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("squash_players.id"), primary_key=True, index=True
    )
    side: Mapped[int] = mapped_column(SmallInteger(), nullable=False)


class Game(Base):
    """One game's score. The last game of a match may still be in play.

    A game scored rally by rally keeps its score equal to the rallies each
    side won, so the rallies are its history and the score its total.
    """

    __tablename__ = "squash_games"
    __table_args__ = (
        UniqueConstraint("match_id", "number", name="uq_squash_games_match_number"),
        CheckConstraint("number > 0", name="number_positive"),
        CheckConstraint(
            "side1_points >= 0 AND side2_points >= 0", name="points_not_negative"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("squash_matches.id", ondelete="CASCADE"), nullable=False
    )
    # 1 for the first game of the match
    number: Mapped[int] = mapped_column(Integer(), nullable=False)
    side1_points: Mapped[int] = mapped_column(SmallInteger(), nullable=False)
    side2_points: Mapped[int] = mapped_column(SmallInteger(), nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.datetime.now
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(),
        nullable=True,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    )

    rallies: Mapped[List["Rally"]] = relationship(
        cascade="all, delete-orphan", order_by="Rally.number"
    )


class Rally(Base):
    """One rally of a game scored live, and who won it.

    A let has no winner: it's replayed, so it's kept only as a record of the
    call.
    """

    __tablename__ = "squash_rallies"
    __table_args__ = (
        UniqueConstraint("game_id", "number", name="uq_squash_rallies_game_number"),
        CheckConstraint("number > 0", name="number_positive"),
        CheckConstraint("won_by_side IN (1, 2)", name="won_by_side_is_a_side"),
        CheckConstraint(
            "decision IS NULL OR decision IN ('let', 'stroke', 'no_let')",
            name="decision_is_a_call",
        ),
        CheckConstraint(
            "(won_by_side IS NULL) = (decision IS NOT NULL AND decision = 'let')",
            name="only_a_let_has_no_winner",
        ),
        CheckConstraint(
            "appealed_by_side IN (1, 2)", name="appealed_by_side_is_a_side"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("squash_games.id", ondelete="CASCADE"), nullable=False
    )
    # 1 for the first rally of the game
    number: Mapped[int] = mapped_column(Integer(), nullable=False)
    # Null for a let
    won_by_side: Mapped[Optional[int]] = mapped_column(SmallInteger(), nullable=True)
    # One of RallyDecision, when a player appealed
    decision: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    # Who appealed, when they did and it's known
    appealed_by_side: Mapped[Optional[int]] = mapped_column(
        SmallInteger(), nullable=True
    )
    # Who served it, when that was recorded
    server_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("squash_players.id"), nullable=True
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.datetime.now
    )
