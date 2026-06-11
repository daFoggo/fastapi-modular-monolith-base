"""Users module - public API contract.

Other modules MUST only import from this package root.
Do NOT import from sub-packages directly (e.g. app.modules.users.repositories).
"""

from app.modules.users.dependencies import get_user_service
from app.modules.users.schemas.users import UserInfo, UserProfileUpdate
from app.modules.users.services.dto import CurrentUser, UserCredentials, UserProfile
from app.modules.users.services.users import UserService

__all__ = [
    "CurrentUser",
    "UserCredentials",
    "UserInfo",
    "UserProfile",
    "UserProfileUpdate",
    "UserService",
    "get_user_service",
]
