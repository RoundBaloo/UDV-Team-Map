from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Alembic Config object
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- импорт моделей (metadata) ---
from app.models import Base  # noqa: E402
target_metadata = Base.metadata

# --- читаем DATABASE_URL из настроек (.env) ---
from app.core.config import settings  # noqa: E402
config.set_main_option("sqlalchemy.url", settings.database_url)


def include_object(object, name, type_, reflected, compare_to):
    """
    Игнорируем автогенерацию для существующих индексов и уникальных констрейнтов,
    чтобы Alembic не пытался «переименовать» их из-за naming_convention.
    """
    if type_ in {"index", "unique_constraint"}:
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_schemas=True,
        include_object=include_object,  # ← важный параметр
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations given a connection (sync function executed on async conn)."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_schemas=True,
        include_object=include_object,  # ← важный параметр
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' (async) mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
