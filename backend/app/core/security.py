from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_async_session
from app.models.employee import Employee
from app.schemas.common import ErrorCode, ErrorResponse

# Парольный контекст:
# 1) pbkdf2_sha256 - кроссплатформенный и без нативных зависимостей (по умолчанию)
# 2) bcrypt - если установлен и рабочий, хэши тоже будут корректно верифицироваться
_pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)

_ALG: str = settings.jwt_algorithm
_SECRET: str = settings.secret_key
_ACCESS_MIN: int = settings.access_token_expire_minutes

_bearer = HTTPBearer(auto_error=True)


def verify_password(plain: str, hashed: str) -> bool:
    """Проверяет соответствие пароля и его хэша.

    Args:
        plain: Пароль в открытом виде.
        hashed: Хэш пароля.

    Returns:
        bool: True, если пароль совпадает с хэшем.
    """
    return _pwd_context.verify(plain, hashed)


def get_password_hash(plain: str) -> str:
    """Возвращает хэш пароля.

    По умолчанию используется алгоритм pbkdf2_sha256.

    Args:
        plain: Пароль в открытом виде.

    Returns:
        str: Хэш пароля.
    """
    # Хэшируем в pbkdf2_sha256 по умолчанию (устойчиво на Windows/Git Bash)
    return _pwd_context.hash(plain)


def create_access_token(
    *,
    subject: str,
    expires_minutes: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Создает JWT access-токен.

    Args:
        subject: Значение claim `sub` (как правило, идентификатор пользователя).
        expires_minutes: Время жизни токена в минутах. Если не задано,
            используется значение из настроек.
        extra_claims: Дополнительные claims, которые нужно добавить в токен.

    Returns:
        str: Сериализованный JWT-токен.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes or _ACCESS_MIN)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, _SECRET, algorithm=_ALG)


def decode_token(token: str) -> dict[str, Any]:
    """Декодирует и валидирует JWT-токен.

    Args:
        token: JWT-токен в виде строки.

    Returns:
        dict[str, Any]: Полезная нагрузка токена.

    Raises:
        HTTPException: Если токен истек или некорректен.
    """
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_TOKEN_EXPIRED,
                message="Срок действия токена истек",
                status=401,
            ).model_dump(),
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_INVALID_TOKEN,
                message="Некорректный токен",
                status=401,
            ).model_dump(),
        )


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    session: AsyncSession = Depends(get_async_session),
) -> Employee:
    """Возвращает текущего пользователя по access-токену.

    Args:
        creds: Учетные данные из заголовка Authorization.
        session: Асинхронная сессия базы данных.

    Returns:
        Employee: ORM-модель текущего пользователя.

    Raises:
        HTTPException: Если токен некорректен, пользователь не найден
            или его учетная запись заблокирована.
    """
    payload = decode_token(creds.credentials)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_INVALID_TOKEN,
                message="В токене отсутствует идентификатор пользователя",
                status=401,
            ).model_dump(),
        )

    user_id = int(sub)
    res = await session.execute(
        select(Employee).where(Employee.id == user_id),
    )
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message="Пользователь не найден",
                status=401,
            ).model_dump(),
        )

    if user.is_blocked:
        raise HTTPException(
            status_code=403,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_ACCOUNT_BLOCKED,
                message="Учетная запись заблокирована",
                status=403,
            ).model_dump(),
        )

    return user
