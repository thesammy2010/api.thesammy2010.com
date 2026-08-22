from typing import Optional
from urllib.parse import ParseResult, urlparse

from pydantic import BaseModel, Field

from src.config import Config


class PaginationParams(BaseModel):
    """Input schema for pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number to fetch.")

    @property
    def offset(self) -> int:
        return (self.page - 1) * Config.DEFAULT_DB_PAGE_SIZE


def validate_optional_url(value: Optional[str]) -> Optional[str]:
    """Normalise an optional URL field.

    Blank values become None, since a sheet or a form will send an empty string
    where it means "not set". Anything else must be an absolute URL.
    """
    if value is None:
        return None

    value = str(value).strip()
    if not value:
        return None

    result: ParseResult = urlparse(value)
    if not all([result.scheme, result.netloc]):
        raise ValueError(f"Invalid URL format: {value}")

    return value
