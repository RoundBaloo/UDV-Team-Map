from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from app.core.config import settings


# создаём async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

# фабрика асинхронных сессий
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# dependency для FastAPI
async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


# совместимость для старого кода (auth и т.д.)
async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
