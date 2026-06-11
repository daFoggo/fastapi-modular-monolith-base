from pydantic import BaseModel, EmailStr, Field

from app.modules.users import UserInfo


class SignIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class SignUp(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=512)


class SignInResponse(BaseModel):
    access_token: str
    expiration: str
    refresh_token: str
    refresh_expiration: str
    user_info: UserInfo


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    expiration: str
    refresh_token: str
    refresh_expiration: str
