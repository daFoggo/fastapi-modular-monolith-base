from fastapi import APIRouter, Depends

from app.common import ResponseSchema
from app.core.security import get_password_hash
from app.modules.auth import get_current_active_user
from app.modules.users import CurrentUser, UserInfo, UserProfileUpdate, UserService
from app.modules.users.dependencies import get_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ResponseSchema[UserInfo])
def get_me(
    user: CurrentUser = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
):
    result = service.get_profile_by_id(user.id)
    return ResponseSchema(
        data=UserInfo.model_validate(result),
        message="User profile fetched successfully",
    )


@router.patch("/me/profile", response_model=ResponseSchema[UserInfo])
def complete_profile(
    payload: UserProfileUpdate,
    user: CurrentUser = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
):
    result = service.complete_profile(
        user_id=user.id,
        name=payload.name,
        email=str(payload.email) if payload.email else None,
        hashed_password=get_password_hash(payload.password)
        if payload.password is not None
        else None,
    )
    return ResponseSchema(
        data=UserInfo.model_validate(result),
        message="User profile updated successfully",
    )
