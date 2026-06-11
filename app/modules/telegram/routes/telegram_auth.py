from fastapi import APIRouter, Depends, Header

from app.common import ResponseSchema
from app.core.config import settings
from app.modules.auth import get_current_active_user
from app.modules.telegram import (
    TelegramAuthError,
    TelegramAuthService,
    TelegramLinkStartResponse,
    TelegramUpdate,
    TelegramWebhookResponse,
    get_telegram_auth_service,
)
from app.modules.users import CurrentUser

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/link/start", response_model=ResponseSchema[TelegramLinkStartResponse])
def start_link(
    user: CurrentUser = Depends(get_current_active_user),
    service: TelegramAuthService = Depends(get_telegram_auth_service),
):
    result = service.start_link(user)
    return ResponseSchema(
        data=TelegramLinkStartResponse(
            link_url=result.link_url,
            expires_at=result.expires_at,
        ),
        message="Telegram link created successfully",
    )


@router.post("/webhook", response_model=ResponseSchema[TelegramWebhookResponse])
def handle_webhook(
    payload: TelegramUpdate,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    service: TelegramAuthService = Depends(get_telegram_auth_service),
):
    if (
        settings.TELEGRAM_WEBHOOK_SECRET_TOKEN
        and x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET_TOKEN
    ):
        raise TelegramAuthError(detail="Invalid Telegram webhook secret.")

    result = service.handle_webhook(payload)
    return ResponseSchema(
        data=TelegramWebhookResponse(ok=result.ok, message=result.message),
        message="Telegram webhook processed successfully",
    )
