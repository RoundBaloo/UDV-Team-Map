from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorDetail, ErrorResponse


class AppError(Exception):
    """Базовое прикладное исключение с кодом и HTTP-статусом."""

    status_code: int = 400
    code: str = "APP_ERROR"
    message: str = "Произошла ошибка."

    def __init__(self, message: str | None = None):
        if message is not None:
            self.message = message
        super().__init__(self.message)


# --- Конкретные ошибки авторизации/доступа ---

class AuthInvalidCredentials(AppError):
    status_code = 401
    code = "AUTH_INVALID_CREDENTIALS"
    message = "Неверный логин или пароль"


class AuthBlocked(AppError):
    status_code = 403
    code = "AUTH_BLOCKED"
    message = "Учетная запись заблокирована"


class AuthUnauthorized(AppError):
    status_code = 401
    code = "AUTH_UNAUTHORIZED"
    message = "Требуется аутентификация"


def register_exception_handlers(app: FastAPI) -> None:
    """Подключает единый формат ошибок для наших AppError."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:  # noqa: WPS430
        payload = ErrorResponse(detail=ErrorDetail(code=exc.code, message=exc.message))
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())
