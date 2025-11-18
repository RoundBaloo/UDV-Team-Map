from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Настройки Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.models import Base  # noqa: E402
from app.core.config import settings  # noqa: E402

target_metadata = Base.metadata

db_url = (
    getattr(settings, "DATABASE_DSN", None)
    or getattr(settings, "DATABASE_URL", None)
)
if not db_url:
    raise RuntimeError(
        "DATABASE_URL или DATABASE_DSN должны быть заданы в .env или Settings"
    )

config.set_main_option("sqlalchemy.url", db_url)


def include_object(object, name, type_, reflected, compare_to):  # type: ignore[override]
    """Исключает индексы и уникальные ограничения из автогенерации."""
    if type_ in {"index", "unique_constraint"}:
        return False
    return True


def run_migrations_offline() -> None:
    """Запускает миграции в офлайн-режиме."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_schemas=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Запускает миграции, используя переданное sync-подключение."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_schemas=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Запускает миграции в онлайн-режиме (async)."""
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
