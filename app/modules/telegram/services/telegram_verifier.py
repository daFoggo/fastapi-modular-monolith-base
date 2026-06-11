import hashlib
import hmac
import logging
from base64 import b64encode
from datetime import UTC, datetime, timedelta

import httpx
import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError

from app.core.config import settings
from app.modules.telegram.exceptions import TelegramAuthError

from .dto import TelegramIdentity

logger = logging.getLogger(__name__)


class TelegramAuthVerifier:
    def verify_login_payload(self, payload: dict[str, str]) -> TelegramIdentity:
        if payload.get("code"):
            return self.verify_authorization_code(
                code=payload["code"],
                redirect_uri=payload.get("redirect_uri"),
                code_verifier=payload.get("code_verifier"),
            )

        if payload.get("id_token"):
            return self.verify_id_token(payload["id_token"])

        if not settings.TELEGRAM_BOT_TOKEN:
            raise TelegramAuthError(detail="Telegram bot token is not configured.")

        received_hash = payload.get("hash")
        if not received_hash:
            raise TelegramAuthError(detail="Telegram auth hash is missing.")

        auth_date = self._parse_auth_date(payload.get("auth_date"))
        self._validate_freshness(auth_date)

        data_check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(payload.items())
            if key != "hash" and value is not None
        )
        secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_hash, received_hash):
            raise TelegramAuthError(detail="Invalid Telegram auth payload.")

        telegram_user_id = payload.get("id")
        if not telegram_user_id:
            raise TelegramAuthError(detail="Telegram user id is missing.")

        return TelegramIdentity(
            telegram_user_id=str(telegram_user_id),
            auth_date=auth_date,
            username=payload.get("username"),
            first_name=payload.get("first_name"),
            last_name=payload.get("last_name"),
            photo_url=payload.get("photo_url"),
            phone_number=payload.get("phone_number"),
        )

    def verify_authorization_code(
        self,
        code: str,
        redirect_uri: str | None,
        code_verifier: str | None,
    ) -> TelegramIdentity:
        if not settings.TELEGRAM_LOGIN_CLIENT_ID:
            raise TelegramAuthError(
                detail="Telegram login client id is not configured."
            )
        if not settings.TELEGRAM_LOGIN_CLIENT_SECRET:
            raise TelegramAuthError(
                detail="Telegram login client secret is not configured."
            )
        if not redirect_uri or not code_verifier:
            raise TelegramAuthError(
                detail="Telegram authorization code payload is incomplete."
            )

        credentials = b64encode(
            f"{settings.TELEGRAM_LOGIN_CLIENT_ID}:{settings.TELEGRAM_LOGIN_CLIENT_SECRET}".encode()
        ).decode()
        try:
            response = httpx.post(
                settings.TELEGRAM_OIDC_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": settings.TELEGRAM_LOGIN_CLIENT_ID,
                    "code_verifier": code_verifier,
                },
                headers={"Authorization": f"Basic {credentials}"},
                timeout=10,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Telegram authorization code exchange failed: status=%s body=%s",
                exc.response.status_code,
                exc.response.text[:500],
            )
            raise TelegramAuthError(
                detail="Telegram authorization code exchange failed."
            ) from exc
        except httpx.HTTPError as exc:
            logger.warning(
                "Telegram authorization code exchange failed: error=%s",
                exc.__class__.__name__,
            )
            raise TelegramAuthError(
                detail="Telegram authorization code exchange failed."
            ) from exc

        id_token = response.json().get("id_token")
        if not id_token:
            raise TelegramAuthError(
                detail="Telegram token response is missing id token."
            )
        return self.verify_id_token(id_token)

    def verify_id_token(self, id_token: str) -> TelegramIdentity:
        if not settings.TELEGRAM_LOGIN_CLIENT_ID:
            raise TelegramAuthError(
                detail="Telegram login client id is not configured."
            )

        try:
            signing_key = PyJWKClient(
                settings.TELEGRAM_OIDC_JWKS_URL
            ).get_signing_key_from_jwt(id_token)
            payload = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256", "ES256", "EdDSA", "ES256K"],
                audience=str(settings.TELEGRAM_LOGIN_CLIENT_ID),
                issuer=settings.TELEGRAM_OIDC_ISSUER,
                leeway=settings.TELEGRAM_OIDC_CLOCK_SKEW_SECONDS,
            )
        except (jwt.PyJWTError, PyJWKClientError) as exc:
            unverified_claims = self._safe_unverified_claims(id_token)
            unverified_header = self._safe_unverified_header(id_token)
            logger.warning(
                "Telegram id token validation failed: "
                "error=%s alg=%s kid=%s iss=%s aud=%s",
                exc.__class__.__name__,
                unverified_header.get("alg"),
                unverified_header.get("kid"),
                unverified_claims.get("iss"),
                unverified_claims.get("aud"),
            )
            raise TelegramAuthError(detail="Invalid Telegram id token.") from exc

        telegram_user_id = payload.get("id") or payload.get("sub")
        if not telegram_user_id:
            raise TelegramAuthError(detail="Telegram user id is missing.")

        name = payload.get("name")
        first_name: str | None = None
        last_name: str | None = None
        if isinstance(name, str) and name:
            parts = name.split(maxsplit=1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else None

        return TelegramIdentity(
            telegram_user_id=str(telegram_user_id),
            auth_date=int(payload.get("iat") or datetime.now(UTC).timestamp()),
            username=payload.get("preferred_username"),
            first_name=first_name,
            last_name=last_name,
            photo_url=payload.get("picture"),
            phone_number=payload.get("phone_number"),
        )

    @staticmethod
    def _parse_auth_date(value: str | None) -> int:
        if not value:
            raise TelegramAuthError(detail="Telegram auth date is missing.")
        try:
            return int(value)
        except ValueError as exc:
            raise TelegramAuthError(detail="Invalid Telegram auth date.") from exc

    @staticmethod
    def _validate_freshness(auth_date: int) -> None:
        auth_datetime = datetime.fromtimestamp(auth_date, UTC)
        now = datetime.now(UTC)
        max_age = timedelta(seconds=settings.TELEGRAM_AUTH_MAX_AGE_SECONDS)
        clock_skew = timedelta(seconds=settings.TELEGRAM_OIDC_CLOCK_SKEW_SECONDS)
        if auth_datetime > now + clock_skew:
            raise TelegramAuthError(detail="Telegram auth payload is from the future.")
        if now - auth_datetime > max_age:
            raise TelegramAuthError(detail="Telegram auth payload is expired.")

    @staticmethod
    def _safe_unverified_claims(id_token: str) -> dict:
        try:
            return jwt.decode(id_token, options={"verify_signature": False})
        except jwt.PyJWTError:
            return {}

    @staticmethod
    def _safe_unverified_header(id_token: str) -> dict:
        try:
            return jwt.get_unverified_header(id_token)
        except jwt.PyJWTError:
            return {}
