from __future__ import annotations

from fastapi import FastAPI

from app.core.errors import register_exception_handlers
from app.api.v1 import auth as auth_api
from app.api.v1.employees_router import router as employees_router
from app.api.v1.photo_moderation_router import router as photo_moderation_router
from app.api.v1.media_router import router as media_router


def create_app() -> FastAPI:
    """Factory FastAPI-приложения."""
    app = FastAPI(
        title="UDV Team Map API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        debug=True,
    )

    register_exception_handlers(app)

    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "ok"}

    # /api/v1/auth/*
    app.include_router(auth_api.router, prefix="/api/v1")

    # /api/v1/employees_router/*
    app.include_router(employees_router, prefix="/api/v1")

    # /api/v1/photo_moderation_router/*
    app.include_router(photo_moderation_router, prefix="/api/v1")

    # /api/v1/media_router/*
    app.include_router(media_router, prefix="/api/v1")

    return app


app = create_app()
