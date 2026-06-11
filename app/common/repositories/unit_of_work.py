from contextlib import AbstractContextManager, nullcontext
from typing import Protocol, TypeVar, cast

from sqlalchemy.orm import Session

from app.common.repositories.base import SessionFactory

RepositoryT = TypeVar("RepositoryT", bound="RepositoryFactory")


class RepositoryFactory(Protocol):
    def __init__(self, session_factory: SessionFactory) -> None: ...


class UnitOfWork:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory
        self._context: AbstractContextManager[Session] | None = None
        self.session: Session | None = None
        self._repositories: dict[type[RepositoryFactory], RepositoryFactory] = {}

    def __enter__(self) -> "UnitOfWork":
        self._context = self._session_factory()
        self.session = self._context.__enter__()
        return self

    def get_repo(self, repository_class: type[RepositoryT]) -> RepositoryT:
        if self.session is None:
            raise RuntimeError("UnitOfWork must be entered first.")

        if repository_class not in self._repositories:
            session = self.session
            self._repositories[repository_class] = repository_class(
                lambda: nullcontext(session)
            )
        return cast(RepositoryT, self._repositories[repository_class])

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.session is None or self._context is None:
            raise RuntimeError("UnitOfWork was not entered.")
        try:
            if exc_type is None:
                self.session.commit()
            else:
                self.session.rollback()
        finally:
            self._context.__exit__(exc_type, exc_value, traceback)
