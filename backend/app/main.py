from __future__ import annotations

from fastapi import FastAPI
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.api.v1 import auth as auth_api


def create_app() -> FastAPI:
    """Factory FastAPI-приложения."""
    app = FastAPI(
        title="UDV Team Map API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    register_exception_handlers(app)
    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        """Быстрая проверка состояния сервиса."""
        return {"status": "ok"}

    app.include_router(auth_api.router, prefix="/api/v1")

    return app


app = create_app()
