from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.models import BaseModel
from app.core.exceptions import DuplicatedError, NotFoundError

ModelT = TypeVar("ModelT", bound=BaseModel)
SessionFactory = Callable[[], AbstractContextManager[Session]]


class BaseRepository[ModelT: BaseModel]:
    def __init__(self, session_factory: SessionFactory, model: type[ModelT]) -> None:
        self.session_factory = session_factory
        self.model = model

    @staticmethod
    def _dump(schema: Any, *, exclude_none: bool = True) -> dict[str, Any]:
        if isinstance(schema, dict):
            return schema
        if hasattr(schema, "model_dump"):
            return schema.model_dump(exclude_none=exclude_none)
        if hasattr(schema, "__dict__"):
            return {
                key: value
                for key, value in vars(schema).items()
                if not key.startswith("_") and (value is not None or not exclude_none)
            }
        return dict(schema)

    @staticmethod
    def _handle_integrity_error(session: Session, error: IntegrityError) -> None:
        session.rollback()
        raise DuplicatedError(detail="Resource already exists.") from error

    def read_by_id(self, item_id: str) -> ModelT:
        with self.session_factory() as session:
            item = session.get(self.model, item_id)
            if item is None:
                raise NotFoundError(detail=f"{self.model.__name__} not found.")
            return item

    def create(self, values: Any, *, auto_commit: bool = True) -> ModelT:
        with self.session_factory() as session:
            item = self.model(**self._dump(values, exclude_none=False))
            try:
                session.add(item)
                if auto_commit:
                    session.commit()
                    session.refresh(item)
                else:
                    session.flush()
            except IntegrityError as error:
                self._handle_integrity_error(session, error)
            return item

    def update(self, item_id: str, values: Any, *, auto_commit: bool = True) -> ModelT:
        with self.session_factory() as session:
            item = session.get(self.model, item_id)
            if item is None:
                raise NotFoundError(detail=f"{self.model.__name__} not found.")
            for key, value in self._dump(values).items():
                setattr(item, key, value)
            try:
                if auto_commit:
                    session.commit()
                    session.refresh(item)
                else:
                    session.flush()
            except IntegrityError as error:
                self._handle_integrity_error(session, error)
            return item

    def delete(self, item_id: str, *, auto_commit: bool = True) -> None:
        with self.session_factory() as session:
            item = session.get(self.model, item_id)
            if item is None:
                raise NotFoundError(detail=f"{self.model.__name__} not found.")
            session.delete(item)
            if auto_commit:
                session.commit()
            else:
                session.flush()
