import datetime
from typing import Optional
from urllib.parse import ParseResult, urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
        nullable=True,
    )
    muscle_group: Optional[str] = Field(
        description="The muscle group targeted by the exercise",
        max_length=100,
        default=None,
        nullable=True,
    )
    specific_muscle: Optional[str] = Field(
        description="The specific muscle targeted by the exercise",
        max_length=100,
        default=None,
        nullable=True,
    )
    bipedal: Optional[bool] = Field(
        description="Indicates if the exercise is bipedal (involving both sides of the body)",
        default=False,
        nullable=False,
    )
    image_url: Optional[str] = Field(
        description="URL of an image representing the exercise",
        max_length=512,
        default=None,
        nullable=True,
    )

    @classmethod
    @field_validator("image_url")
    def image_url_is_valid(cls, value: Optional[str]) -> Optional[str]:
        result: ParseResult = urlparse(value)
        if all([result.scheme, result.netloc]):
            return value

        raise ValueError(f"Invalid URL format: {result}")

    free_weights: Optional[bool] = Field(
        description="Indicates if the exercise uses free weights or not",
        default=False,
        nullable=False,
    )


class ExerciseRequest(_BaseExercise):
    pass


class ExerciseResponse(_BaseExercise):
    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
