from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UserProfile:
    id: str
    name: str
    email: str | None
    avatar_url: str | None = None
    created_at: datetime | None = None
    profile_completed: bool = True


@dataclass(frozen=True)
class UserCredentials:
    id: str
    name: str
    email: str | None
    hashed_password: str | None
    is_active: bool


@dataclass(frozen=True)
class CurrentUser:
    id: str
    name: str
    email: str | None
    is_active: bool
