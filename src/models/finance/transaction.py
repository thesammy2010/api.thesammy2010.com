import datetime
import decimal
import uuid
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import ForeignKey

from src.models import Base


class Transaction(Base):
    """A single spend.

    Imported rows keep the id written into the sheet's ID column, so that
    re-importing updates them rather than adding them again.
    """

    __tablename__ = "finance_transactions"
    __table_args__ = (
        CheckConstraint(
            "(related_to_id IS NULL) = (relation IS NULL)",
            name="relation_set_with_related_to",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    spent_on: Mapped[datetime.date] = mapped_column(Date(), nullable=False, index=True)
    # Four places rather than two: a spend split on Splitwise can come to a
    # fraction of a penny, and rounding each one would drift the totals.
    amount_gbp: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    # What was charged in the local currency, for a spend made abroad
    original_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(14, 4), nullable=True
    )
    original_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)

    payment_method_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("finance_payment_methods.id"), nullable=False
    )
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("finance_merchants.id"), nullable=True
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("finance_categories.id"), nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # The spend this one belongs to, such as the purchase a foreign transaction
    # fee was charged for, so the fee can be counted towards its true cost.
    # Only one level deep: a spend with this set can't have its own.
    related_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("finance_transactions.id"), nullable=True, index=True
    )
    # One of TransactionRelation, stored as its value. Set exactly when
    # related_to_id is.
    relation: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # Only recorded from 2026, so null means unknown rather than no
    is_necessary: Mapped[Optional[bool]] = mapped_column(Boolean(), nullable=True)
    is_recurring: Mapped[Optional[bool]] = mapped_column(Boolean(), nullable=True)
    with_partner: Mapped[Optional[bool]] = mapped_column(Boolean(), nullable=True)
    # One of TimeOfDay, stored as its value
    time_of_day: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

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
        return f"<Transaction(id={self.id}, spent_on={self.spent_on}, amount_gbp={self.amount_gbp})>"
