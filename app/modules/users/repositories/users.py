from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, cast

from sqlalchemy.orm import Session

from app.common import BaseRepository
from app.modules.users.models.user import User


class UserRepository(BaseRepository[User]):
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        super().__init__(session_factory=session_factory, model=User)

    def read_by_email(self, email: str) -> User | None:
        with self.session_factory() as session:
            return session.query(User).filter(User.email == email).first()

    def read_optional_by_id(self, user_id: str) -> User | None:
        with self.session_factory() as session:
            return session.get(User, user_id)

    def create(self, schema: Any, *, auto_commit: bool = True) -> User:
        return cast(User, super().create(schema, auto_commit=auto_commit))
