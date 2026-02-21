import base64
import binascii
import enum
import logging
import os
from tempfile import NamedTemporaryFile
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Environment(enum.Enum):
    LOCAL = "local"
    DEV = "dev"
    PRODUCTION = "prod"


def get_env(override: Optional[str] = None) -> Optional[Environment]:
    try:
        return Environment(override or os.getenv("ENV"))
    except ValueError:
        return None


class Config:
    DATABASE_URL: str = os.getenv("DATABASE_URL").replace(
        "postgres://", "postgresql+psycopg://"
    )
    ENVIRONMENT: Environment = Environment(os.getenv("ENVIRONMENT", "local"))
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
                logging.error(
                    f"Could not decode base64 encoded service account json: {sa_json}"
                )
        return None

    def __init__(self, env: Environment = get_env()) -> None:
        self.env = env
        self.google_service_account_filepath: str = (
            self._parse_google_service_account_json()
        )
