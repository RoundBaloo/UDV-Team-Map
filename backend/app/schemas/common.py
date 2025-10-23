from __future__ import annotations

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Деталь ошибки в машинном виде + человекочитаемое сообщение.

    Attributes:
        code: Короткий код ошибки (для фронта/логики), например 'AUTH_INVALID_CREDENTIALS'.
        message: Текст, который можно показать пользователю.
    """
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Стандартный ответ с ошибкой."""
    detail: ErrorDetail
