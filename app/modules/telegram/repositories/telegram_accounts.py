from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, cast

from sqlalchemy.orm import Session, joinedload

from app.common import BaseRepository
from app.modules.telegram.models.telegram_account import TelegramAccount


class TelegramAccountRepository(BaseRepository[TelegramAccount]):
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        super().__init__(session_factory=session_factory, model=TelegramAccount)

    def read_by_telegram_user_id(
        self, telegram_user_id: str, eager_user: bool = False
    ) -> TelegramAccount | None:
        with self.session_factory() as session:
            query = session.query(TelegramAccount).filter(
                TelegramAccount.telegram_user_id == telegram_user_id
            )
            if eager_user:
                query = query.options(joinedload(TelegramAccount.user))
            return query.first()

    def read_by_user_id(self, user_id: str) -> TelegramAccount | None:
        with self.session_factory() as session:
            return (
                session.query(TelegramAccount)
                .filter(TelegramAccount.user_id == user_id)
                .first()
            )

    def create(self, schema: Any, *, auto_commit: bool = True) -> TelegramAccount:
        return cast(TelegramAccount, super().create(schema, auto_commit=auto_commit))

    def update(
        self,
        id: str,
        schema: Any,
        *,
        auto_commit: bool = True,
    ) -> TelegramAccount:
        return cast(
            TelegramAccount,
            super().update(id, schema, auto_commit=auto_commit),
        )
