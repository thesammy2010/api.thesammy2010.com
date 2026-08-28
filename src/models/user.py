import uuid
from typing import Optional

from sqlalchemy import Index, event, func
from sqlalchemy.engine.base import Connection
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime, String

from src.models import Base


class User(Base):
    __tablename__ = "users"
    # A google_account_id must be unique only among active (non-deleted)
    # users - deleting a user frees up their google_account_id so they (or
    # anyone re-provisioned under that identity) can sign up fresh, while
    # the deleted row is kept around for its audit trail.
    __table_args__ = (
        Index(
            "uq_users_google_account_id_active",
            "google_account_id",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    google_account_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # One of guest/viewer/editor/admin (src.common.UserRole). Kept as a plain
    # string rather than a DB enum, consistent with how the other enums in
    # this codebase are only validated at the API layer, not the DB layer.
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="guest"
    )
    # NULL means active. Users are never hard-deleted via the API so their
    # audit trail and any records they created stay intact; deletion just
    # sets this and provisioning/auth treat the row as gone.
    deleted_at: Mapped[Optional[uuid.UUID]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    created_at: Mapped[uuid.UUID] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[uuid.UUID] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    # Set whenever their token is resolved to this row (create_user_in_db),
    # so it reflects the last time they authenticated, not just the last
    # time they touched any endpoint. NULL for a row an admin pre-provisioned
    # that nobody has signed into yet.
    last_signed_in_at: Mapped[Optional[uuid.UUID]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.google_account_id})>"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@event.listens_for(User, "before_insert")
def update(mapper: Mapper, connection: Connection, target: User):
    target.updated_at = func.now()


class UserAuditLog(Base):
    """Records every admin-initiated create/delete/role-change on a user.

    Deliberately flat (actor/target/action/before/after) rather than a
    generic JSON payload - there are exactly three action kinds today, and
    plain columns keep the log directly queryable.
    """

    __tablename__ = "user_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    # One of created/deleted/role_changed.
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    previous_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[uuid.UUID] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
