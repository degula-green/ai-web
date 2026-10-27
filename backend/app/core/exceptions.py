from __future__ import annotations

from fastapi import status


class AppError(Exception):
    def __init__(self, message: str, *, code: str = "app_error", status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="not_found", status_code=status.HTTP_404_NOT_FOUND)


class StateTransitionError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="invalid_state_transition", status_code=status.HTTP_409_CONFLICT)


class ConfigurationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="configuration_error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContractError(Exception):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
