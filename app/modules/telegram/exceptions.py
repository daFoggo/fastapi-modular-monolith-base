from app.core.exceptions import (
    AuthError,
    DuplicatedError,
    ExternalServiceError,
    ValidationError,
)


class TelegramAuthError(AuthError):
    pass


class TelegramValidationError(ValidationError):
    pass


class TelegramDuplicatedError(DuplicatedError):
    pass


class TelegramServiceError(ExternalServiceError):
    pass
