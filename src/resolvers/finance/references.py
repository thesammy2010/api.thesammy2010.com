import uuid
from typing import Optional, Type

from src.db import session
from src.models import Base


class ReferenceNotFound(LookupError):
    """Raised when a request refers to a row that doesn't exist."""


class DuplicateName(ValueError):
    """Raised when a name that has to be unique is already taken."""


def require_reference(model: Type[Base], row_id: Optional[uuid.UUID], label: str):
    """Check a referenced row exists, so a bad id is a 404 rather than a 500."""
    if row_id is not None and session.get(model, row_id) is None:
        raise ReferenceNotFound(f"{label} {row_id} not found")
