from __future__ import annotations

from fastapi import FastAPI

from app.core.errors import register_exception_handlers
from app.api import auth as auth_api

from app.api.employees_router import router as employees_router
from app.api.photo_moderation_router import router as photo_moderation_router
from app.api.media_router import router as media_router
from app.api.org_router import router as org_router


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

    # /api/auth/*
    app.include_router(auth_api.router, prefix="/api")

    # /api/employees_router/*
    app.include_router(employees_router, prefix="/api")

    # /api/photo_moderation_router/*
    app.include_router(photo_moderation_router, prefix="/api")

    # /api/media_router/*
    app.include_router(media_router, prefix="/api")

    app.include_router(org_router, prefix="/api")

    return app


app = create_app()
