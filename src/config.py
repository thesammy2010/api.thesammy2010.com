import base64
import binascii
import enum
import logging
import os
from tempfile import NamedTemporaryFile
from typing import Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class Environment(enum.Enum):
    LOCAL = "local"
    DEV = "dev"
    PRODUCTION = "prod"


class Config:
    # Absent when the app is only being imported rather than served, such as
    # in the tests. The session is opened on first use, so this is only
    # required by the time something actually talks to the database.
    DATABASE_URL: Optional[str] = (
        os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql+psycopg://")
        or None
    )
    ENVIRONMENT: Environment = Environment(os.getenv("ENVIRONMENT", "local"))
    # Lets local/dev testing skip verifying a real Google token. Ignored in
    # prod regardless of the env var, so it can never be left on by accident.
    DISABLE_AUTH: bool = (
        os.getenv("DISABLE_AUTH", "false").lower() == "true"
        and ENVIRONMENT != Environment.PRODUCTION
    )
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    DEFAULT_DB_PAGE_SIZE: int = int(os.getenv("DEFAULT_DB_PAGE_SIZE", "50"))
    GOOGLE_SPREADSHEET_ID: str = os.getenv("GOOGLE_SPREADSHEET_ID")
    GOOGLE_SERVICE_ACCOUNT_JSON_BASE64: str = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_JSON_BASE64"
    )

    def _parse_google_service_account_json(self) -> Optional[str]:
        if sa_json := self.GOOGLE_SERVICE_ACCOUNT_JSON_BASE64:
            try:
                buffer: bytes = base64.b64decode(sa_json)
                with NamedTemporaryFile(mode="wb", delete=False) as f:
                    f.write(buffer)
                    return f.name
            except binascii.Error:
                logger.error(
                    f"Could not decode base64 encoded service account json: {sa_json}"
                )
        return None

    def __init__(self) -> None:
        self.google_service_account_filepath: str = (
            self._parse_google_service_account_json()
        )
