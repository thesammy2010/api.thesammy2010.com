import logging

import sqlalchemy
from sqlalchemy.orm import Session

from src.config import Config
from src.models import Base
from src.models.squash.user import User  # noqa: F401


def init_db(cfg: Config) -> Session:
    engine = sqlalchemy.create_engine(
        cfg.DATABASE_URL,
        echo=False if cfg.ENVIRONMENT == cfg.ENVIRONMENT.PRODUCTION else True,
    )
    logging.debug("Initializing database")

    engine.connect()
    logging.debug("Database initialized")

    Base.metadata.create_all(engine)
    logging.debug("Database tables created")

    return sqlalchemy.orm.sessionmaker(bind=engine)()


session = init_db(Config())
