from uuid import uuid4

from app.core.exceptions import AuthError, DuplicatedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    get_password_hash,
    verify_password,
)
from app.modules.auth.services.dto import (
    RefreshTokenCommand,
    SignInCommand,
    SignInResult,
    SignUpCommand,
    TokenResult,
)
from app.modules.users import UserProfile, UserService


class AuthService:
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    def sign_up(self, command: SignUpCommand) -> UserProfile:
        existing_user = self._user_service.get_credentials_by_email(command.email)
        if existing_user:
            raise DuplicatedError(detail="Email already exists.")

        return self._user_service.create_user(
            email=command.email,
            hashed_password=get_password_hash(command.password),
            name=command.name,
            avatar_url=command.avatar_url,
            user_token=uuid4().hex,
        )

    def sign_in(self, command: SignInCommand) -> SignInResult:
        user = self._user_service.get_credentials_by_email(command.email)
        if not user:
            raise AuthError(detail="Email does not exist.")

        if not user.is_active:
            raise AuthError(detail="User is inactive.")

        if not user.hashed_password or not verify_password(
            command.password, user.hashed_password
        ):
            raise AuthError(detail="Incorrect password.")

        profile = self._user_service.get_profile_by_id(user.id)
        if profile is None:
            raise AuthError(detail="User not found.")
        return self.issue_session(profile)

    def refresh_token(self, command: RefreshTokenCommand) -> TokenResult:
        decoded = decode_jwt(command.refresh_token)
        if not decoded or decoded.get("type") != "refresh":
            raise AuthError(detail="Invalid refresh token.")

        user_id = decoded.get("sub")
        if not user_id:
            raise AuthError(detail="Invalid token payload.")

        user = self._user_service.get_credentials_by_id(user_id)
        if not user:
            raise AuthError(detail="User not found.")

        if not user.is_active:
            raise AuthError(detail="User is inactive.")

        subject = self._build_token_subject(user.id, user.email, user.name)
        access_token, expiration = create_access_token(subject)
        refresh_token, refresh_expiration = create_refresh_token(subject)

        return TokenResult(
            access_token=access_token,
            expiration=expiration,
            refresh_token=refresh_token,
            refresh_expiration=refresh_expiration,
        )

    def issue_session(self, user_profile: UserProfile) -> SignInResult:
        subject = self._build_token_subject(
            user_profile.id, user_profile.email, user_profile.name
        )
        access_token, expiration = create_access_token(subject)
        refresh_token, refresh_expiration = create_refresh_token(subject)
        return SignInResult(
            access_token=access_token,
            expiration=expiration,
            refresh_token=refresh_token,
            refresh_expiration=refresh_expiration,
            user_info=user_profile,
        )

    @staticmethod
    def _build_token_subject(user_id: str, email: str | None, name: str) -> dict:
        return {
            "sub": str(user_id),
            "email": email,
            "name": name,
        }
