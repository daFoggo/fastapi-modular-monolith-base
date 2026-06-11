from typing import Any

from fastapi import HTTPException, status


class AppError(HTTPException):
    def __init__(self, status_code: int, detail: Any = None) -> None:
        super().__init__(status_code=status_code, detail=detail)


class DuplicatedError(AppError):
    def __init__(self, detail: Any = "Resource already exists.") -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)


class AuthError(AppError):
    def __init__(self, detail: Any = "Authentication failed.") -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail)


class NotFoundError(AppError):
    def __init__(self, detail: Any = "Resource not found.") -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class ValidationError(AppError):
    def __init__(self, detail: Any = "Request validation failed.") -> None:
        super().__init__(status.HTTP_422_UNPROCESSABLE_CONTENT, detail)


class ExternalServiceError(AppError):
    def __init__(self, detail: Any = "External service request failed.") -> None:
        super().__init__(status.HTTP_502_BAD_GATEWAY, detail)


class ConfigurationError(AppError):
    def __init__(self, detail: Any = "Application configuration is invalid.") -> None:
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail)
