import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    muscle_group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    specific_muscle: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bipedal: Mapped[bool] = mapped_column(nullable=False, default=False)
    free_weights: Mapped[bool] = mapped_column(nullable=False, default=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

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
        return f"<Exercise(name={self.name}, description={self.description}>"
