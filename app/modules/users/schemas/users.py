from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserInfo(BaseModel):
    id: str
    name: str
    email: EmailStr | None = None
    avatar_url: str | None = Field(default=None)
    created_at: datetime | None = Field(default=None)
    profile_completed: bool = True

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)
