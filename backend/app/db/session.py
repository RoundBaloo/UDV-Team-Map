from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from typing import AsyncGenerator

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: отдает асинхронную сессию БД и корректно её закрывает."""
    from app.db.session import AsyncSessionLocal  # локальный импорт, чтобы избежать циклов
    async with AsyncSessionLocal() as session:
        yield session