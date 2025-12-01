from __future__ import annotations

"""Служебный скрипт для очистки рабочих таблиц в dev/test-среде."""

import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import create_async_engine

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from app.core.config import settings  # noqa: E402

CANDIDATE_TABLES = [
    "audit_log",
    "sync_record",
    "photo_moderation",
    "employee_team",
    "employee",
    "media",
    "org_unit",
    "external_entity_snapshot",
    "sync_job",
]


async def main() -> None:
    """Очищает данные в рабочих таблицах (TRUNCATE ... RESTART IDENTITY CASCADE)."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        isolation_level="AUTOCOMMIT",
    )

    async with engine.begin() as conn:
        res = await conn.exec_driver_sql(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public';",
        )
        existing_tables = {row[0] for row in res}

        to_truncate = [t for t in CANDIDATE_TABLES if t in existing_tables]

        if not to_truncate:
            print("Нет ни одной подходящей таблицы для TRUNCATE.")
            await engine.dispose()
            return

        sql = f"TRUNCATE {', '.join(to_truncate)} RESTART IDENTITY CASCADE"
        await conn.exec_driver_sql(sql)
        print(f"Data truncated for tables: {', '.join(to_truncate)}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
