import logging

import sqlalchemy
from sqlalchemy.orm import Session

from src.config import Config


def init_db(cfg: Config) -> Session:
    engine = sqlalchemy.create_engine(
        cfg.DATABASE_URL,
        echo=False if cfg.ENVIRONMENT == cfg.ENVIRONMENT.PRODUCTION else True,
    )
    logging.debug("Initializing database")

    engine.connect()
    logging.debug("Database initialized")

    return sqlalchemy.orm.sessionmaker(bind=engine)()


session = init_db(Config())
