from typing import Any

import httpx

from app.core.config import settings
from app.modules.telegram.exceptions import (
    TelegramServiceError,
    TelegramValidationError,
)


class TelegramBotClient:
    def __init__(self, bot_token: str | None = None) -> None:
        self._bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: str | None = None,
        reply_markup: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": False,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._post("sendMessage", payload)

    def _post(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._bot_token:
            raise TelegramValidationError(
                detail="Telegram bot token is not configured."
            )

        url = f"{settings.TELEGRAM_BOT_API_BASE_URL}/bot{self._bot_token}/{method}"
        try:
            response = httpx.post(url, json=payload, timeout=10)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TelegramServiceError(
                detail="Telegram Bot API request failed."
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise TelegramServiceError(
                detail="Telegram Bot API returned invalid JSON."
            ) from exc
        if not data.get("ok"):
            description = data.get("description", "Unknown Telegram Bot API error")
            raise TelegramServiceError(detail=description)
        return data
