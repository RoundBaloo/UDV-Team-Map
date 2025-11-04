# app/schemas/common.py
from __future__ import annotations

from enum import StrEnum
from typing import Any, Optional, List

from pydantic import BaseModel


class ErrorCode(StrEnum):
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
    """
    Одна конкретная ошибка.
    - code: машинный код (см. ErrorCode)
    - message: человекочитаемое сообщение
    - field: для ошибок валидации (например, 'email')
    - hint: необязательный совет, что можно сделать
    """
    code: str  # допускаем и произвольные коды, чтобы не ломаться при расширении
    message: str
    field: Optional[str] = None
    hint: Optional[str] = None


class ErrorResponse(BaseModel):
    """
    Стандартный ответ с ошибкой.
    Совместим с существующим форматом: поле `detail` остаётся.
    Можно вернуть несколько ошибок списком в `errors`.
    Дополнительно: status, request_id, meta.
    """
    # старое поле (оставляем для совместимости)
    detail: Optional[ErrorDetail] = None

    # новое — поддержка нескольких ошибок
    errors: Optional[List[ErrorDetail]] = None

    # полезные доп. поля
    status: Optional[int] = None
    request_id: Optional[str] = None
    meta: Optional[dict[str, Any]] = None

    @classmethod
    def single(
        cls,
        *,
        code: ErrorCode | str,
        message: str,
        status: Optional[int] = None,
        field: Optional[str] = None,
        hint: Optional[str] = None,
        request_id: Optional[str] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> "ErrorResponse":
        """Удобный конструктор для одной ошибки."""
        return cls(
            detail=ErrorDetail(code=str(code), message=message, field=field, hint=hint),
            status=status,
            request_id=request_id,
            meta=meta,
        )

    @classmethod
    def multiple(
        cls,
        details: List[ErrorDetail],
        *,
        status: Optional[int] = None,
        request_id: Optional[str] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> "ErrorResponse":
        """Удобный конструктор для нескольких ошибок."""
        return cls(
            errors=details,
            status=status,
            request_id=request_id,
            meta=meta,
        )
