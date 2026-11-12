from typing import List

from src.db import session
from src.models.finance import Category as DBCategory


def get_categories() -> List[DBCategory]:
    return session.query(DBCategory).order_by(DBCategory.group, DBCategory.name).all()
