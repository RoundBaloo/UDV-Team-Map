from __future__ import annotations

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Входные данные для авторизации.

    Attributes:
        email: Корпоративная почта пользователя.
        password: Пароль в открытом виде.
    """
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Ответ при успешной авторизации.

    Attributes:
        access_token: JWT access-токен.
        token_type: Тип токена (по умолчанию 'bearer').
    """
    access_token: str
    token_type: str = "bearer"
