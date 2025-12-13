import datetime
import uuid
from typing import Optional

import pendulum
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import ForeignKey

from src.models import Base


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid(), nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id"), nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id"), nullable=False
    )
    workout_time: Mapped[pendulum.DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    index: Mapped[int] = mapped_column(nullable=False)
    repetitions: Mapped[int] = mapped_column(nullable=False)
    weight_kg: Mapped[float] = mapped_column(nullable=False)
    bar_weight_kg: Mapped[float] = mapped_column(nullable=True)
    supplementary_weight_kg: Mapped[float] = mapped_column(nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

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
        return f"<Workout(index={self.index}, weight={self.weight_kg}, reps{self.repetitions}>"
