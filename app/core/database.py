from collections.abc import Generator
from contextlib import contextmanager
from importlib import import_module

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.common import BaseModel

MODEL_MODULES = (
    "app.modules.users.models.user",
    "app.modules.telegram.models.telegram_account",
    "app.modules.telegram.models.telegram_link_session",
)


class Database:
    def __init__(self, db_url: str) -> None:
        engine_kwargs: dict = {"echo": False}
        if db_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
            if ":memory:" in db_url:
                engine_kwargs["poolclass"] = StaticPool

        self._engine = create_engine(db_url, **engine_kwargs)
        self._session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=self._engine, expire_on_commit=False
        )

    def create_database(self) -> None:
        for module_name in MODEL_MODULES:
            import_module(module_name)
        BaseModel.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
