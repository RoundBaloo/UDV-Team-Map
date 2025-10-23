from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import bcrypt
from jose import jwt, JWTError

from app.core.config import settings

ALLOWED_ALGS = {"HS256"}
ALGORITHM = (
    settings.jwt_algorithm if settings.jwt_algorithm in ALLOWED_ALGS else "HS256"
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, соответствует ли пароль хешу из БД.

    Args:
        plain_password: Пароль в открытом виде.
        hashed_password: Bcrypt-хеш (строка) из БД.

    Returns:
        True, если пароль корректен, иначе False.
    """
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    """Создает bcrypt-хеш пароля (используется при первичной загрузке из AD).

    Args:
        password: Пароль в открытом виде.

    Returns:
        Строка с bcrypt-хешем.
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_access_token(
    data: Dict[str, Any], expires_minutes: int | None = None
) -> str:
    """Создает JWT access-токен с ограниченным временем жизни.

    Args:
        data: Полезная нагрузка (например, {"sub": "<user_id>"}).
        expires_minutes: Время жизни токена в минутах. Если не задано,
            берется из настроек.

    Returns:
        Строка с JWT.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Проверяет подпись и декодирует JWT.

    Args:
        token: JWT-токен из заголовка Authorization.

    Returns:
        Раскодированная полезная нагрузка.

    Raises:
        JWTError: если подпись/срок действия некорректны.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
