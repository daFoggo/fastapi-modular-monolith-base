from fastapi import APIRouter, Depends

from app.common import ResponseSchema
from app.modules.telegram import (
    TelegramAuthService,
    TelegramLoginCommand,
    TelegramLoginRequest,
    get_telegram_auth_service,
)
from app.modules.users import UserInfo

from ..dependencies import get_auth_service
from ..schemas import (
    RefreshTokenRequest,
    SignIn,
    SignInResponse,
    SignUp,
    TokenResponse,
)
from ..services import (
    AuthService,
    RefreshTokenCommand,
    SignInCommand,
    SignUpCommand,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sign-up", response_model=ResponseSchema[UserInfo])
def sign_up(payload: SignUp, service: AuthService = Depends(get_auth_service)):
    result = service.sign_up(
        SignUpCommand(
            email=str(payload.email),
            password=payload.password,
            name=payload.name,
            avatar_url=payload.avatar_url,
        )
    )
    return ResponseSchema(
        data=UserInfo.model_validate(result),
        message="User registered successfully",
    )


@router.post("/sign-in", response_model=ResponseSchema[SignInResponse])
def sign_in(payload: SignIn, service: AuthService = Depends(get_auth_service)):
    result = service.sign_in(
        SignInCommand(email=str(payload.email), password=payload.password)
    )
    return ResponseSchema(
        data=SignInResponse(
            access_token=result.access_token,
            expiration=result.expiration,
            refresh_token=result.refresh_token,
            refresh_expiration=result.refresh_expiration,
            user_info=UserInfo.model_validate(result.user_info),
        ),
        message="Login successful",
    )


@router.post("/refresh", response_model=ResponseSchema[TokenResponse])
def refresh_token(
    payload: RefreshTokenRequest, service: AuthService = Depends(get_auth_service)
):
    result = service.refresh_token(RefreshTokenCommand(payload.refresh_token))
    return ResponseSchema(
        data=TokenResponse(
            access_token=result.access_token,
            expiration=result.expiration,
            refresh_token=result.refresh_token,
            refresh_expiration=result.refresh_expiration,
        ),
        message="Token refreshed successfully",
    )


@router.post("/telegram", response_model=ResponseSchema[SignInResponse])
def telegram_sign_in(
    payload: TelegramLoginRequest,
    service: TelegramAuthService = Depends(get_telegram_auth_service),
):
    result = service.sign_in(
        TelegramLoginCommand(
            payload={
                key: str(value)
                for key, value in payload.model_dump(exclude_none=True).items()
            }
        )
    )
    return ResponseSchema(
        data=SignInResponse(
            access_token=result.access_token,
            expiration=result.expiration,
            refresh_token=result.refresh_token,
            refresh_expiration=result.refresh_expiration,
            user_info=UserInfo.model_validate(result.user_info),
        ),
        message="Telegram login successful",
    )
