"""Auth module - public API contract.

Other modules MUST only import from this package root.
Do NOT import from sub-packages directly (e.g. app.modules.auth.services).
"""

from app.modules.auth.dependencies import (
    get_auth_service,
    get_current_active_user,
)
from app.modules.auth.services.auth import AuthService
from app.modules.auth.services.dto import SignInResult

__all__ = [
    "AuthService",
    "SignInResult",
    "get_auth_service",
    "get_current_active_user",
]
