import enum
import os

from dotenv import load_dotenv

load_dotenv()


class Environment(enum.Enum):
    LOCAL = "local"
    DEV = "dev"
    PRODUCTION = "prod"


class Config:
    DATABASE_URL: str = os.getenv("DATABASE_URL").replace(
        "postgres://", "postgresql+psycopg://"
    )
    ENVIRONMENT: Environment = Environment(os.getenv("ENVIRONMENT", "local"))
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
