import datetime
import uuid
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class PaymentMethod(Base):
    """The card, account or other means a spend was paid with."""

    __tablename__ = "finance_payment_methods"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    # One of PaymentMethodKind, stored as its value like users.role
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)

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
        return f"<PaymentMethod(id={self.id}, name={self.name}, kind={self.kind})>"
