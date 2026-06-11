from contextlib import AbstractContextManager, nullcontext

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common import UnitOfWork
from app.core.dependencies import get_db
from app.modules.auth import AuthService, get_auth_service
from app.modules.telegram.repositories.telegram_accounts import (
    TelegramAccountRepository,
)
from app.modules.telegram.repositories.telegram_link_sessions import (
    TelegramLinkSessionRepository,
)
from app.modules.telegram.services.bot_client import TelegramBotClient
from app.modules.telegram.services.telegram_auth import TelegramAuthService
from app.modules.telegram.services.telegram_verifier import TelegramAuthVerifier
from app.modules.users import UserService, get_user_service


def get_telegram_auth_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> TelegramAuthService:
    def session_factory() -> AbstractContextManager[Session]:
        return nullcontext(db)

    telegram_account_repository = TelegramAccountRepository(session_factory)
    telegram_link_session_repository = TelegramLinkSessionRepository(session_factory)
    return TelegramAuthService(
        user_service=user_service,
        telegram_account_repository=telegram_account_repository,
        telegram_link_session_repository=telegram_link_session_repository,
        verifier=TelegramAuthVerifier(),
        bot_client=TelegramBotClient(),
        auth_service=auth_service,
        unit_of_work_factory=lambda: UnitOfWork(session_factory),
    )
