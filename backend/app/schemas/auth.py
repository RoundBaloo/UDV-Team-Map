from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Запрос на вход по email и паролю."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Ответ с JWT-токеном доступа."""

    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    """Краткая информация о текущем пользователе."""

    employee_id: int = Field(
        serialization_alias="employee_id",
        validation_alias="id",
    )
    email: EmailStr
    first_name: str
    last_name: str
    title: str | None = None
    is_admin: bool
    is_blocked: bool
