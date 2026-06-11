import base64
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.core.config import settings
from app.modules.telegram.exceptions import TelegramAuthError
from app.modules.telegram.services.dto import TelegramIdentity
from app.modules.telegram.services.telegram_verifier import TelegramAuthVerifier


def test_authorization_code_exchange_uses_pkce(monkeypatch) -> None:
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_ID", "client-id")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_SECRET", "client-secret")
    captured = {}
    expected = TelegramIdentity("123", 1_700_000_000)

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"id_token": "jwt-token"}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    verifier = TelegramAuthVerifier()
    monkeypatch.setattr(
        "app.modules.telegram.services.telegram_verifier.httpx.post", fake_post
    )
    monkeypatch.setattr(verifier, "verify_id_token", lambda token: expected)

    identity = verifier.verify_authorization_code(
        "code", "https://app/callback", "verifier"
    )

    credentials = base64.b64encode(b"client-id:client-secret").decode()
    assert identity == expected
    assert captured["headers"]["Authorization"] == f"Basic {credentials}"
    assert captured["data"]["code_verifier"] == "verifier"


def test_authorization_code_exchange_failure_is_auth_error(monkeypatch) -> None:
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_ID", "client-id")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_SECRET", "client-secret")

    def fail(*args, **kwargs):
        raise httpx.ConnectError("failed")

    monkeypatch.setattr(
        "app.modules.telegram.services.telegram_verifier.httpx.post", fail
    )
    with pytest.raises(TelegramAuthError):
        TelegramAuthVerifier().verify_authorization_code(
            "code", "https://app/callback", "verifier"
        )


def test_widget_payload_rejects_future_timestamp(monkeypatch) -> None:
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "token")
    future = int((datetime.now(UTC) + timedelta(hours=1)).timestamp())

    with pytest.raises(TelegramAuthError, match="future"):
        TelegramAuthVerifier().verify_login_payload(
            {"id": "1", "auth_date": str(future), "hash": "invalid"}
        )


def test_id_token_decode_checks_configured_claims(monkeypatch) -> None:
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_ID", "client-id")
    captured = {}

    class SigningKey:
        key = "public-key"

    class JwkClient:
        def __init__(self, url):
            captured["url"] = url

        def get_signing_key_from_jwt(self, token):
            return SigningKey()

    def fake_decode(*args, **kwargs):
        captured["kwargs"] = kwargs
        return {"sub": "123", "iat": 1_700_000_000}

    monkeypatch.setattr(
        "app.modules.telegram.services.telegram_verifier.PyJWKClient", JwkClient
    )
    monkeypatch.setattr(
        "app.modules.telegram.services.telegram_verifier.jwt.decode", fake_decode
    )

    identity = TelegramAuthVerifier().verify_id_token("token")

    assert identity.telegram_user_id == "123"
    assert captured["kwargs"]["audience"] == "client-id"
    assert captured["kwargs"]["issuer"] == settings.TELEGRAM_OIDC_ISSUER
