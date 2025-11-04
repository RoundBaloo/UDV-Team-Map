from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, create_access_token
from app.models.employee import Employee
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import ErrorResponse, ErrorCode


async def _get_employee_by_email(session: AsyncSession, email: str) -> Employee | None:
    res = await session.execute(select(Employee).where(Employee.email == email))
    return res.scalar_one_or_none()


async def login_service(session: AsyncSession, payload: LoginRequest) -> TokenResponse:
    """
    Логин по email и паролю.
    Возвращает JWT или структурированную ошибку в формате ErrorResponse.
    """
    user = await _get_employee_by_email(session, payload.email)

    def raise_error(code: ErrorCode, message: str, status_code: int):
        raise HTTPException(
            status_code=status_code,
            detail=ErrorResponse.single(
                code=code,
                message=message,
                status=status_code,
            ).model_dump(),
        )

    # одинаковая ошибка, чтобы не палить, существует ли email
    if not user or not user.password_hash:
        raise_error(ErrorCode.AUTH_INVALID_CREDENTIALS, "Invalid credentials", 401)

    if not verify_password(payload.password, user.password_hash):
        raise_error(ErrorCode.AUTH_INVALID_CREDENTIALS, "Invalid credentials", 401)

    if user.is_blocked:
        raise_error(ErrorCode.AUTH_ACCOUNT_BLOCKED, "Account blocked", 403)

    # всё ок
    user.last_login_at = datetime.now(timezone.utc)
    await session.commit()

    token = create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email, "is_admin": user.is_admin},
    )

    return TokenResponse(access_token=token, token_type="bearer")
