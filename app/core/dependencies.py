from collections.abc import Generator
from functools import lru_cache

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Database


@lru_cache
def get_database() -> Database:
    return Database(settings.DATABASE_URI)


def get_db() -> Generator[Session, None, None]:
    with get_database().session() as session:
        yield session
