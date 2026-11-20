import datetime
import uuid

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import ForeignKey

from src.models import Base


class Device(Base):
    """A phone signed in to one of the apps, for sending it notifications.

    Keyed on the push token Apple gives the app, which is unique to that
    install of that app. A phone that signs in as someone else moves to
    them, so it's only ever told about one user's things.
    """

    __tablename__ = "devices"
    __table_args__ = (
        CheckConstraint(
            "environment IN ('sandbox', 'production')", name="environment_is_known"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    # The APNs device token, as lowercase hex
    token: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    # The app's bundle ID, which a push is addressed to
    app: Mapped[str] = mapped_column(String(255), nullable=False)
    # One of DeviceEnvironment, stored as its value: which of Apple's push
    # servers the token belongs to, sandbox for a build run from Xcode
    environment: Mapped[str] = mapped_column(String(16), nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.datetime.now
    )
    # Every launch registers again, so a token not seen for a long while is
    # one the app has stopped using
    last_registered_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(), nullable=False, default=datetime.datetime.now
    )

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, app={self.app})>"
