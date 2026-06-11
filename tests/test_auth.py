from app.core.security import create_refresh_token
from app.modules.users.models import User


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
