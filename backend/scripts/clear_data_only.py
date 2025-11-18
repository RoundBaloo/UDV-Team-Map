from __future__ import annotations

"""
Временный служебный скрипт.

Назначение:
- очистить рабочие таблицы проекта в БД (TRUNCATE ... RESTART IDENTITY CASCADE),
  не трогая схему и миграции.
Использовать только вручную в дев/тест-среде.
"""

import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


# Добавляем корень проекта в sys.path, чтобы работали импортируемые модули app.*
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Таблицы, которые очищаем
TABLES = [
    "audit_log",
    "sync_record",
    "photo_moderation",
    "employee",
    "media",
    "org_unit",
    "external_entity_snapshot",
    "sync_job",
]

SQL = f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"


async def main() -> None:
    engine = create_async_engine(
        settings.DATABASE_URL,
        isolation_level="AUTOCOMMIT",
    )
    async with engine.begin() as conn:
        await conn.exec_driver_sql(SQL)
        print("Data truncated (RESTART IDENTITY CASCADE).")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
