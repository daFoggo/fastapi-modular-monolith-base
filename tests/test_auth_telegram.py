import hashlib
import hmac
from datetime import UTC, datetime

import pytest

from app.core.config import settings
from app.core.security import create_refresh_token
from app.modules.telegram.models import TelegramAccount
from app.modules.telegram.repositories.telegram_accounts import (
    TelegramAccountRepository,
)
from app.modules.users.models import User


def telegram_payload(telegram_id: str = "987654321") -> dict[str, str]:
    payload = {
        "id": telegram_id,
        "first_name": "Tele",
        "last_name": "User",
        "username": "teleuser",
        "auth_date": str(int(datetime.now(UTC).timestamp())),
    }
    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(payload.items())
    )
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
    payload["hash"] = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    return payload


def sign_up_and_in(client, email: str = "user@example.com") -> tuple[str, str]:
    password = "password123"
    sign_up = client.post(
        "/api/v1/auth/sign-up",
        json={"email": email, "password": password, "name": "Test User"},
    )
    assert sign_up.status_code == 200
    sign_in = client.post(
        "/api/v1/auth/sign-in",
        json={"email": email, "password": password},
    )
    assert sign_in.status_code == 200
    data = sign_in.json()["data"]
    return data["access_token"], data["refresh_token"]


def test_email_auth_and_current_profile(client, database) -> None:
    database.create_database()
    access_token, refresh_token = sign_up_and_in(client)

    me = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    refreshed = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )

    assert me.status_code == 200
    assert me.json()["data"]["email"] == "user@example.com"
    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["access_token"]


def test_auth_rejects_wrong_token_types(client, database) -> None:
    database.create_database()
    access_token, refresh_token = sign_up_and_in(client, "types@example.com")

    current_user = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})

    assert current_user.status_code == 401
    assert refresh.status_code == 401


def test_duplicate_email_and_profile_completion(client, database, monkeypatch) -> None:
    database.create_database()
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "telegram-test-token")
    sign_up_and_in(client, "existing@example.com")
    telegram_login = client.post("/api/v1/auth/telegram", json=telegram_payload("222"))
    token = telegram_login.json()["data"]["access_token"]

    duplicate = client.patch(
        "/api/v1/users/me/profile",
        json={"email": "existing@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    completed = client.patch(
        "/api/v1/users/me/profile",
        json={"email": "telegram@example.com", "password": "password123"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert duplicate.status_code == 400
    assert completed.status_code == 200
    assert completed.json()["data"]["profile_completed"] is True


def test_telegram_login_is_atomic(client, database, monkeypatch) -> None:
    database.create_database()
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "telegram-test-token")

    def fail_create(*args, **kwargs):
        raise RuntimeError("account insert failed")

    monkeypatch.setattr(TelegramAccountRepository, "create", fail_create)

    with pytest.raises(RuntimeError, match="account insert failed"):
        client.post("/api/v1/auth/telegram", json=telegram_payload("atomic"))

    with database.session() as session:
        assert session.query(User).count() == 0
        assert session.query(TelegramAccount).count() == 0


def test_telegram_login_reuses_account(client, database, monkeypatch) -> None:
    database.create_database()
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "telegram-test-token")

    first = client.post("/api/v1/auth/telegram", json=telegram_payload("111"))
    second_payload = telegram_payload("111")
    second_payload["username"] = "changed"
    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(second_payload.items())
        if key != "hash"
    )
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
    second_payload["hash"] = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    second = client.post("/api/v1/auth/telegram", json=second_payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert (
        first.json()["data"]["user_info"]["id"]
        == second.json()["data"]["user_info"]["id"]
    )


def test_telegram_link_token_is_one_time(client, database, monkeypatch) -> None:
    database.create_database()
    monkeypatch.setattr(settings, "TELEGRAM_BOT_USERNAME", "test_bot")
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET_TOKEN", None)
    access_token, _ = sign_up_and_in(client, "link@example.com")
    link = client.post(
        "/api/v1/telegram/link/start",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    token = link.json()["data"]["link_url"].rsplit("=", 1)[1]
    update = {
        "message": {
            "text": f"/start {token}",
            "from": {"id": 333, "first_name": "Linked"},
        }
    }

    first = client.post("/api/v1/telegram/webhook", json=update)
    second = client.post("/api/v1/telegram/webhook", json=update)

    assert first.status_code == 200
    assert second.status_code == 422


def test_telegram_login_payload_requires_exactly_one_mode(client, database) -> None:
    database.create_database()

    missing = client.post("/api/v1/auth/telegram", json={})
    mixed = client.post(
        "/api/v1/auth/telegram",
        json={
            "id_token": "token",
            "code": "code",
            "redirect_uri": "x",
            "code_verifier": "y",
        },
    )

    assert missing.status_code == 422
    assert mixed.status_code == 422


def test_webhook_secret_and_basic_command(client, database, monkeypatch) -> None:
    database.create_database()
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "telegram-test-token")
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET_TOKEN", "webhook-secret")
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {"ok": True, "result": {"message_id": 1}}

        return Response()

    monkeypatch.setattr(
        "app.modules.telegram.services.bot_client.httpx.post", fake_post
    )
    rejected = client.post(
        "/api/v1/telegram/webhook",
        json={"message": {"text": "/help", "chat": {"id": 1}}},
    )
    accepted = client.post(
        "/api/v1/telegram/webhook",
        json={"message": {"text": "/help", "chat": {"id": 1}}},
        headers={"X-Telegram-Bot-Api-Secret-Token": "webhook-secret"},
    )

    assert rejected.status_code == 401
    assert accepted.status_code == 200
    assert calls[0][1]["chat_id"] == 1


def test_inactive_user_cannot_use_refreshed_session(client, database) -> None:
    database.create_database()
    _, refresh_token = sign_up_and_in(client, "inactive@example.com")
    with database.session() as session:
        user = session.query(User).filter(User.email == "inactive@example.com").one()
        user.is_active = False
        session.commit()

    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 401


def test_refresh_rejects_unknown_user(client, database) -> None:
    database.create_database()
    token, _ = create_refresh_token(
        {"sub": "missing", "email": None, "name": "Missing"}
    )
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert response.status_code == 401
