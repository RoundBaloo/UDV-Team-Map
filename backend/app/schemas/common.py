from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class ErrorCode(StrEnum):
    """Коды ошибок верхнего уровня."""

    # Аутентификация / авторизация
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_ACCOUNT_BLOCKED = "AUTH_ACCOUNT_BLOCKED"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"

    # Общее
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    # Синхронизация
    SYNC_ALREADY_RUNNING = "SYNC_ALREADY_RUNNING"
    SYNC_SOURCE_ERROR = "SYNC_SOURCE_ERROR"
    SYNC_VALIDATION_ERROR = "SYNC_VALIDATION_ERROR"


class ErrorDetail(BaseModel):
    """Описание одной конкретной ошибки.

    - code: машинный код (см. ErrorCode)
    - message: человекочитаемое сообщение
    - field: для ошибок валидации (например, "email")
    - hint: необязательный совет, что можно сделать
    """

    # Допускаем произвольные строковые коды, чтобы не ломаться при расширении.
    code: str
    message: str
    field: str | None = None
    hint: str | None = None


class ErrorResponse(BaseModel):
    """Стандартный ответ с ошибкой.

    Совместим с существующим форматом: поле `detail` остаётся.
    Можно вернуть несколько ошибок списком в `errors`.
    Дополнительно: status, request_id, meta.
    """

    detail: ErrorDetail | None = None

    errors: list[ErrorDetail] | None = None

    status: int | None = None
    request_id: str | None = None
    meta: dict[str, Any] | None = None

    @classmethod
    def single(
        cls,
        *,
        code: ErrorCode | str,
        message: str,
        status: int | None = None,
        field: str | None = None,
        hint: str | None = None,
        request_id: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ErrorResponse:
        """Удобный конструктор для одной ошибки."""
        return cls(
            detail=ErrorDetail(
                code=str(code),
                message=message,
                field=field,
                hint=hint,
            ),
            status=status,
            request_id=request_id,
            meta=meta,
        )

    @classmethod
    def multiple(
        cls,
        details: list[ErrorDetail],
        *,
        status: int | None = None,
        request_id: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ErrorResponse:
        """Удобный конструктор для нескольких ошибок."""
        return cls(
            errors=details,
            status=status,
            request_id=request_id,
            meta=meta,
        )
