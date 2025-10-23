from __future__ import annotations

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token
from app.core.errors import AuthInvalidCredentials, AuthBlocked
from app.models.employee import Employee


async def authenticate_user(
    credentials: LoginRequest,
    session: AsyncSession,
) -> Employee | None:
    """Проверяет, существует ли пользователь и совпадает ли пароль."""
    result = await session.execute(
        select(Employee).where(Employee.email == credentials.email)
    )
    user: Employee | None = result.scalar_one_or_none()

    if not user:
        return None

    if not verify_password(credentials.password, user.password_hash):
        return None

    return user


async def login_service(
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """
    Проверяет email и пароль, выдает JWT-токен.

    Raises:
        AuthInvalidCredentials: если логин или пароль неверные.
        AuthBlocked: если учетная запись заблокирована.
    """
    user = await authenticate_user(credentials, session)
    if not user:
        raise AuthInvalidCredentials()

    if user.is_blocked:
        raise AuthBlocked()

    access_token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token)
