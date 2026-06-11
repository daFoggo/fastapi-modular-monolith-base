from dataclasses import dataclass

from app.modules.users import UserProfile


@dataclass(frozen=True)
class SignUpCommand:
    email: str
    password: str
    name: str
    avatar_url: str | None = None


@dataclass(frozen=True)
class SignInCommand:
    email: str
    password: str


@dataclass(frozen=True)
class RefreshTokenCommand:
    refresh_token: str


@dataclass(frozen=True)
class SignInResult:
    access_token: str
    expiration: str
    refresh_token: str
    refresh_expiration: str
    user_info: UserProfile


@dataclass(frozen=True)
class TokenResult:
    access_token: str
    expiration: str
    refresh_token: str
    refresh_expiration: str
