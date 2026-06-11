from typing import Any, cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthError
from app.core.security import decode_jwt
from app.modules.auth.services import AuthService
from app.modules.users import CurrentUser, UserService, get_user_service


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    return AuthService(user_service=user_service)


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Any:
        credentials = cast(
            HTTPAuthorizationCredentials | None,
            await super().__call__(request),
        )
        if credentials:
            if credentials.scheme.lower() != "bearer":
                raise AuthError(detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise AuthError(detail="Invalid token or expired token.")
            return credentials.credentials
        raise AuthError(detail="Invalid authorization code.")

    def verify_jwt(self, jwt_token: str) -> bool:
        payload = decode_jwt(jwt_token)
        return bool(payload and payload.get("type") == "access")


def get_bearer_token(token: str = Depends(JWTBearer())) -> str:
    return token


def get_token_payload(token: str = Depends(get_bearer_token)) -> dict[str, Any]:
    payload = decode_jwt(token)
    if not payload or payload.get("type") != "access":
        raise AuthError(detail="Invalid token payload.")
    return payload


def get_current_user(
    payload: dict[str, Any] = Depends(get_token_payload),
    user_service: UserService = Depends(get_user_service),
) -> CurrentUser:
    user_id = payload.get("sub")
    if not user_id:
        raise AuthError(detail="Invalid token payload.")

    user = user_service.get_current_user(str(user_id))
    if not user:
        raise AuthError(detail="User not found.")
    return user


def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if not current_user.is_active:
        raise AuthError(detail="Inactive user.")
    return current_user
