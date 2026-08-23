import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.schemas.utils import validate_optional_url


class _BaseExercise(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(
        description="Name of the exercise",
        max_length=255,
    )
    description: Optional[str] = Field(
        description="Description of the exercise",
        max_length=255,
        default=None,
    )
    muscle_group: Optional[str] = Field(
        description="The muscle group targeted by the exercise",
        max_length=100,
        default=None,
    )
    specific_muscle: Optional[str] = Field(
        description="The specific muscle targeted by the exercise",
        max_length=100,
        default=None,
    )
    bipedal: Optional[bool] = Field(
        description="Indicates if the exercise is bipedal (involving both sides of the body)",
        default=False,
    )
    image_url: Optional[str] = Field(
        description="URL of an image representing the exercise",
        max_length=512,
        default=None,
    )

    @field_validator("image_url", mode="before")
    @classmethod
    def image_url_is_valid(cls, value: Optional[str]) -> Optional[str]:
        return validate_optional_url(value)

    free_weights: Optional[bool] = Field(
        description="Indicates if the exercise uses free weights or not",
        default=False,
    )


class ExerciseRequest(_BaseExercise):
    pass


class ExerciseResponse(_BaseExercise):
    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
