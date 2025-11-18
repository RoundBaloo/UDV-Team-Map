from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.models.employee import Employee
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import ErrorCode, ErrorResponse


async def _get_employee_by_email(
    session: AsyncSession,
    email: str,
) -> Employee | None:
    """Возвращает сотрудника по email или None, если не найден."""
    res = await session.execute(
        select(Employee).where(Employee.email == email),
    )
    return res.scalar_one_or_none()


async def login_service(
    session: AsyncSession,
    payload: LoginRequest,
) -> TokenResponse:
    """Логин по email и паролю, возвращает JWT или HTTPException с ErrorResponse."""
    user = await _get_employee_by_email(session, payload.email)

    def raise_error(code: ErrorCode, message: str, status_code: int) -> None:
        raise HTTPException(
            status_code=status_code,
            detail=ErrorResponse.single(
                code=code,
                message=message,
                status=status_code,
            ).model_dump(),
        )

    if not user or not user.password_hash:
        raise_error(
            ErrorCode.AUTH_INVALID_CREDENTIALS,
            "Invalid credentials",
            status.HTTP_401_UNAUTHORIZED,
        )

    if not verify_password(payload.password, user.password_hash):
        raise_error(
            ErrorCode.AUTH_INVALID_CREDENTIALS,
            "Invalid credentials",
            status.HTTP_401_UNAUTHORIZED,
        )

    if user.is_blocked:
        raise_error(
            ErrorCode.AUTH_ACCOUNT_BLOCKED,
            "Account blocked",
            status.HTTP_403_FORBIDDEN,
        )

    user.last_login_at = datetime.now(timezone.utc)
    await session.commit()

    token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "email": user.email,
            "is_admin": user.is_admin,
        },
    )
    return TokenResponse(access_token=token, token_type="bearer")
