from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, cast

from sqlalchemy.orm import Session

from app.common import BaseRepository
from app.modules.telegram.models.telegram_link_session import TelegramLinkSession


class TelegramLinkSessionRepository(BaseRepository[TelegramLinkSession]):
    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        super().__init__(session_factory=session_factory, model=TelegramLinkSession)

    def read_by_token(self, token: str) -> TelegramLinkSession | None:
        with self.session_factory() as session:
            return (
                session.query(TelegramLinkSession)
                .filter(TelegramLinkSession.token == token)
                .first()
            )

    def create(self, schema: Any, *, auto_commit: bool = True) -> TelegramLinkSession:
        return cast(
            TelegramLinkSession, super().create(schema, auto_commit=auto_commit)
        )

    def update(
        self,
        id: str,
        schema: Any,
        *,
        auto_commit: bool = True,
    ) -> TelegramLinkSession:
        return cast(
            TelegramLinkSession,
            super().update(id, schema, auto_commit=auto_commit),
        )
