from __future__ import annotations

from fastapi import APIRouter
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import ErrorResponse
from app.services.auth import login_service

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account blocked"},
    },
)
async def login_endpoint(payload: LoginRequest):
    """Логин по email и паролю. Возвращает JWT access-токен."""
    return await login_service(payload)
