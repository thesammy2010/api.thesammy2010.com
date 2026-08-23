import logging
from typing import Any, Optional

import sqlalchemy
from sqlalchemy.orm import Session

from src.config import Config

logger = logging.getLogger(__name__)

_session: Optional[Session] = None


def init_db(cfg: Config) -> Session:
    if not cfg.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set, cannot connect to the database")

    engine = sqlalchemy.create_engine(
        cfg.DATABASE_URL,
    )
    logger.debug("Initializing database")

    engine.connect()
    logger.debug("Database initialized")

    return sqlalchemy.orm.sessionmaker(bind=engine)()


def get_session() -> Session:
    """The shared session, opened the first time something asks for it."""
    global _session
    if _session is None:
        _session = init_db(Config())

    return _session


class _LazySession:
    """Stands in for the session until something actually uses it.

    Connecting while this module is imported means nothing that reaches a
    resolver can be imported without a database, which is why none of the
    endpoints could be tested. Everything still does `from src.db import
    session`, but the connection is now opened on first use.
    """

    def __getattr__(self, name: str) -> Any:
        return getattr(get_session(), name)


session = _LazySession()
