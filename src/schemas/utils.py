from pydantic import BaseModel, Field

from src.config import Config


class PaginationParams(BaseModel):
    """Input schema for pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number to fetch.")

    @property
    def offset(self) -> int:
        return (self.page - 1) * Config.DEFAULT_DB_PAGE_SIZE
