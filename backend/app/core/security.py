from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_async_session
from app.models.employee import Employee
from app.schemas.common import ErrorResponse, ErrorCode

# Парольный контекст:
# 1) pbkdf2_sha256 — кросс-платформенно и без нативных зависимостей (по умолчанию)
# 2) bcrypt — если установлен/рабочий, тоже будет корректно верифицироваться
_pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)

def get_password_hash(plain: str) -> str:
    # хэшируем в pbkdf2_sha256 по умолчанию (устойчиво на Windows/Git Bash)
    return _pwd_context.hash(plain)

_ALG = settings.jwt_algorithm
_SECRET = settings.secret_key
_ACCESS_MIN = settings.access_token_expire_minutes

def create_access_token(
    *,
    subject: str,
    expires_minutes: Optional[int] = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes or _ACCESS_MIN)
    payload: dict[str, Any] = {"sub": subject, "exp": expire, "iat": now, "type": "access"}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, _SECRET, algorithm=_ALG)

def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_TOKEN_EXPIRED,
                message="Token expired",
                status=401,
            ).model_dump(),
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_INVALID_TOKEN,
                message="Invalid token",
                status=401,
            ).model_dump(),
        )

_bearer = HTTPBearer(auto_error=True)

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    session: AsyncSession = Depends(get_async_session),
) -> Employee:
    payload = decode_token(creds.credentials)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_INVALID_TOKEN,
                message="Missing token subject",
                status=401,
            ).model_dump(),
        )

    user_id = int(sub)
    res = await session.execute(select(Employee).where(Employee.id == user_id))
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message="User not found",
                status=401,
            ).model_dump(),
        )

    if user.is_blocked:
        raise HTTPException(
            status_code=403,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_ACCOUNT_BLOCKED,
                message="Account blocked",
                status=403,
            ).model_dump(),
        )

    return user
