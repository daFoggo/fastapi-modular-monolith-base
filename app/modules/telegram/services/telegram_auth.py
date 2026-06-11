from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import uuid4

from app.common import UnitOfWork
from app.core.config import settings
from app.modules.auth import AuthService, SignInResult
from app.modules.telegram.exceptions import (
    TelegramAuthError,
    TelegramDuplicatedError,
    TelegramValidationError,
)
from app.modules.telegram.repositories.telegram_accounts import (
    TelegramAccountRepository,
)
from app.modules.telegram.repositories.telegram_link_sessions import (
    TelegramLinkSessionRepository,
)
from app.modules.telegram.schemas import TelegramUpdate
from app.modules.telegram.services.bot_client import TelegramBotClient
from app.modules.telegram.services.dto import (
    TelegramIdentity,
    TelegramLinkStartResult,
    TelegramLoginCommand,
    TelegramWebhookResult,
)
from app.modules.telegram.services.telegram_verifier import TelegramAuthVerifier
from app.modules.users import CurrentUser, UserService

UnitOfWorkFactory = Callable[[], UnitOfWork]


class TelegramAuthService:
    def __init__(
        self,
        user_service: UserService,
        auth_service: AuthService,
        telegram_account_repository: TelegramAccountRepository,
        telegram_link_session_repository: TelegramLinkSessionRepository,
        verifier: TelegramAuthVerifier,
        bot_client: TelegramBotClient,
        unit_of_work_factory: UnitOfWorkFactory,
    ) -> None:
        self._user_service = user_service
        self._auth_service = auth_service
        self._telegram_account_repository = telegram_account_repository
        self._telegram_link_session_repository = telegram_link_session_repository
        self._verifier = verifier
        self._bot_client = bot_client
        self._unit_of_work_factory = unit_of_work_factory

    def sign_in(self, command: TelegramLoginCommand) -> SignInResult:
        identity = self._verifier.verify_login_payload(command.payload)
        account = self._telegram_account_repository.read_by_telegram_user_id(
            identity.telegram_user_id
        )

        if account:
            current_user = self._user_service.get_current_user(account.user_id)
            if current_user is None:
                raise TelegramAuthError(detail="Linked user was not found.")
            if not current_user.is_active:
                raise TelegramAuthError(detail="User is inactive.")
            self._update_account_from_identity(account.id, identity)
            profile = self._user_service.get_profile_by_id(account.user_id)
            if profile is None:
                raise TelegramAuthError(detail="Linked user was not found.")
            return self._auth_service.issue_session(profile)

        profile = self._create_telegram_user(identity)
        return self._auth_service.issue_session(profile)

    def start_link(self, user: CurrentUser) -> TelegramLinkStartResult:
        if not settings.TELEGRAM_BOT_USERNAME:
            raise TelegramValidationError(
                detail="Telegram bot username is not configured."
            )
        if self._telegram_account_repository.read_by_user_id(user.id):
            raise TelegramDuplicatedError(detail="Telegram account is already linked.")

        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.TELEGRAM_LINK_TOKEN_EXPIRE_MINUTES
        )
        token = token_urlsafe(32)
        self._telegram_link_session_repository.create(
            {
                "token": token,
                "user_id": user.id,
                "expires_at": expires_at,
                "consumed_at": None,
            }
        )
        return TelegramLinkStartResult(
            link_url=f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={token}",
            expires_at=expires_at.isoformat(),
        )

    def handle_webhook(self, update: TelegramUpdate) -> TelegramWebhookResult:
        if update.callback_query is not None:
            return TelegramWebhookResult(ok=True, message="Callback ignored")

        message = update.message
        if message is None:
            return TelegramWebhookResult(ok=True, message="Update ignored")

        text = (message.text or "").strip()
        chat_id = message.chat.id if message.chat else None
        telegram_user = message.from_user

        if text.startswith("/start "):
            token = text.split(maxsplit=1)[1].strip()
            if not token:
                raise TelegramValidationError(detail="Telegram link token is missing.")
            if telegram_user is None:
                raise TelegramValidationError(detail="Telegram user id is missing.")
            identity = TelegramIdentity(
                telegram_user_id=str(telegram_user.id),
                auth_date=int(datetime.now(UTC).timestamp()),
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
            )
            self._consume_link_token(token, identity)
            if chat_id is not None:
                self._bot_client.send_message(
                    chat_id,
                    "Telegram account linked successfully. "
                    "You can return to the web app.",
                )
            return TelegramWebhookResult(ok=True, message="Telegram account linked")

        response_text = self._build_command_response(text)
        if response_text and chat_id is not None:
            self._bot_client.send_message(chat_id, response_text, parse_mode="HTML")
        return TelegramWebhookResult(ok=True, message="Update processed")

    def _create_telegram_user(self, identity: TelegramIdentity):
        with self._unit_of_work_factory() as unit_of_work:
            account_repository = unit_of_work.get_repo(TelegramAccountRepository)
            profile = self._user_service.create_user(
                email=None,
                hashed_password=None,
                name=self._build_display_name(identity),
                avatar_url=identity.photo_url,
                user_token=uuid4().hex,
                profile_completed=False,
                auto_commit=False,
            )
            account_repository.create(
                self._account_values(profile.id, identity),
                auto_commit=False,
            )
        return profile

    def _consume_link_token(self, token: str, identity: TelegramIdentity) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            account_repository = unit_of_work.get_repo(TelegramAccountRepository)
            link_repository = unit_of_work.get_repo(TelegramLinkSessionRepository)
            link_session = link_repository.read_by_token(token)
            if link_session is None:
                raise TelegramValidationError(detail="Telegram link token is invalid.")
            if link_session.consumed_at:
                raise TelegramValidationError(
                    detail="Telegram link token was already used."
                )
            if self._as_aware_datetime(link_session.expires_at) < datetime.now(UTC):
                raise TelegramValidationError(detail="Telegram link token is expired.")
            if account_repository.read_by_user_id(link_session.user_id):
                raise TelegramDuplicatedError(
                    detail="Telegram account is already linked."
                )
            if account_repository.read_by_telegram_user_id(identity.telegram_user_id):
                raise TelegramDuplicatedError(
                    detail="Telegram account belongs to another user."
                )

            account_repository.create(
                self._account_values(link_session.user_id, identity),
                auto_commit=False,
            )
            link_repository.update(
                link_session.id,
                {"consumed_at": datetime.now(UTC)},
                auto_commit=False,
            )

    def _update_account_from_identity(
        self, account_id: str, identity: TelegramIdentity
    ) -> None:
        self._telegram_account_repository.update(
            account_id,
            {
                "username": identity.username,
                "first_name": identity.first_name,
                "last_name": identity.last_name,
                "photo_url": identity.photo_url,
                "phone_number": identity.phone_number,
                "last_auth_at": datetime.now(UTC),
            },
        )

    @staticmethod
    def _account_values(user_id: str, identity: TelegramIdentity) -> dict:
        return {
            "user_id": user_id,
            "telegram_user_id": identity.telegram_user_id,
            "username": identity.username,
            "first_name": identity.first_name,
            "last_name": identity.last_name,
            "photo_url": identity.photo_url,
            "phone_number": identity.phone_number,
            "last_auth_at": datetime.now(UTC),
        }

    @staticmethod
    def _build_display_name(identity: TelegramIdentity) -> str:
        full_name = " ".join(
            part for part in (identity.first_name, identity.last_name) if part
        ).strip()
        return (
            full_name
            or identity.username
            or f"Telegram User {identity.telegram_user_id}"
        )

    @staticmethod
    def _build_command_response(text: str) -> str | None:
        command = text.split(maxsplit=1)[0].split("@", 1)[0]
        frontend_url = settings.FRONTEND_URL.rstrip("/")
        if command == "/start":
            return (
                "<b>Welcome.</b>\n\n"
                "Use the web application to sign in or connect this "
                "Telegram account.\n\n"
                f'<a href="{frontend_url}">Open web application</a>'
            )
        if command == "/help":
            return (
                "<b>Telegram connection</b>\n\n"
                "Sign in to the web application, open account settings, then start "
                "the Telegram connection flow."
            )
        if command == "/settings":
            return (
                "<b>Account settings</b>\n\n"
                f'<a href="{frontend_url}/settings">Open account settings</a>'
            )
        return None

    @staticmethod
    def _as_aware_datetime(value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)
