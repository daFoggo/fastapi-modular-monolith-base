from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramIdentity:
    telegram_user_id: str
    auth_date: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    photo_url: str | None = None
    phone_number: str | None = None


@dataclass(frozen=True)
class TelegramLoginCommand:
    payload: dict[str, str]


@dataclass(frozen=True)
class TelegramLinkStartResult:
    link_url: str
    expires_at: str


@dataclass(frozen=True)
class TelegramWebhookResult:
    ok: bool
    message: str
