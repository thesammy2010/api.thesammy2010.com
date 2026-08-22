import logging

import sqlalchemy
from sqlalchemy.orm import Session

from src.config import Config

logger = logging.getLogger(__name__)


def init_db(cfg: Config) -> Session:
    engine = sqlalchemy.create_engine(
        cfg.DATABASE_URL,
    )
    logger.debug("Initializing database")

    engine.connect()
    logger.debug("Database initialized")

    return sqlalchemy.orm.sessionmaker(bind=engine)()


session = init_db(Config())
