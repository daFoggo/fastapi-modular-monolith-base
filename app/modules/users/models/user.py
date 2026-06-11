from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common import BaseModel


class User(BaseModel):
    email: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    profile_completed: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
