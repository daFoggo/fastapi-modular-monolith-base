from app.modules.telegram.dependencies import get_telegram_auth_service
from app.modules.telegram.exceptions import TelegramAuthError
from app.modules.telegram.schemas import (
    TelegramLinkStartResponse,
    TelegramLoginRequest,
    TelegramUpdate,
    TelegramWebhookResponse,
)
from app.modules.telegram.services.dto import TelegramLoginCommand
from app.modules.telegram.services.telegram_auth import TelegramAuthService

__all__ = [
    "TelegramAuthError",
    "TelegramAuthService",
    "TelegramLinkStartResponse",
    "TelegramLoginCommand",
    "TelegramLoginRequest",
    "TelegramUpdate",
    "TelegramWebhookResponse",
    "get_telegram_auth_service",
]
