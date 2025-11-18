from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_async_session
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse
from app.services.auth import login_service

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Логин по email и паролю, возвращает JWT",
)
async def login_endpoint(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    """Авторизация пользователя по email и паролю.

    Args:
        payload: Данные для входа пользователя.
        session: Асинхронная сессия базы данных.

    Returns:
        TokenResponse: Модель с данными JWT-токена.
    """
    return await login_service(session, payload)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Текущий пользователь по JWT",
)
async def me_endpoint(
    current_user=Depends(get_current_user),
) -> MeResponse:
    """Возвращает информацию о текущем пользователе.

    Args:
        current_user: Текущий пользователь, извлеченный из JWT.

    Returns:
        MeResponse: Данные профиля текущего пользователя.
    """
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        title=current_user.title,
        is_admin=current_user.is_admin,
        is_blocked=current_user.is_blocked,
    )
