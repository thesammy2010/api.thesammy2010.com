import datetime
import decimal
import uuid
from typing import Optional

from sqlalchemy import DateTime, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import ForeignKey

from src.models import Base


class Budget(Base):
    """How much a category is meant to cost each month of one year."""

    __tablename__ = "finance_budgets"
    __table_args__ = (UniqueConstraint("category_id", "year"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("finance_categories.id"), nullable=False
    )
    year: Mapped[int] = mapped_column(nullable=False)
    monthly_target_gbp: Mapped[decimal.Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    # How the target was arrived at, such as "5x/month @ £30"
    rationale: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

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
        return f"<Budget(category_id={self.category_id}, year={self.year}, monthly_target_gbp={self.monthly_target_gbp})>"
