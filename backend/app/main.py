from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 

from app.api import auth as auth_api
from app.api.employees_router import router as employees_router
from app.api.media_router import router as media_router
from app.api.org_router import router as org_router
from app.api.photo_moderation_router import router as photo_moderation_router
from app.core.errors import register_exception_handlers


def create_app() -> FastAPI:
    """Создаёт и настраивает экземпляр FastAPI-приложения."""
    app = FastAPI(
        title="UDV Team Map API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        debug=True,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        """Простой health-check эндпоинт."""
        return {"status": "ok"}

    app.include_router(auth_api.router, prefix="/api")
    app.include_router(employees_router, prefix="/api")
    app.include_router(photo_moderation_router, prefix="/api")
    app.include_router(media_router, prefix="/api")
    app.include_router(org_router, prefix="/api")

    return app


app = create_app()
