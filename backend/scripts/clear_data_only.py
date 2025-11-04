# scripts/clear_data_only.py
from __future__ import annotations

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

# Набор таблиц, которые хотим очистить
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

async def main():
    engine = create_async_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with engine.begin() as conn:
        await conn.exec_driver_sql(SQL)
        print("✅ Data truncated (RESTART IDENTITY CASCADE).")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
