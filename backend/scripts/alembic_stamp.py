from __future__ import annotations

"""
Временный служебный скрипт.

Назначение:
- проставить нужный revision в таблицу alembic_version на удалённой БД,
  если по какой-то причине миграции/алембик не в консистентном состоянии.
Использовать только вручную, под нужный DATABASE_URL и ALEMBIC_HEAD.
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

DATABASE_URL = (
    "postgresql+asyncpg://flooruser:17HjvfPfryjv@89.208.14.204:5432/floordb"
)

ALEMBIC_HEAD = "7a0f90e24afe"

CREATE_VERSION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL
)
"""

DELETE_ALL_SQL = "DELETE FROM alembic_version"
INSERT_SQL_TEMPLATE = "INSERT INTO alembic_version (version_num) VALUES ('{}')"


async def main() -> None:
    engine = create_async_engine(
        DATABASE_URL,
        isolation_level="AUTOCOMMIT",
    )

    async with engine.begin() as conn:  # type: AsyncConnection
        print("Ensuring alembic_version table exists...")
        await conn.exec_driver_sql(CREATE_VERSION_TABLE_SQL)

        print(f"Stamping alembic_version with {ALEMBIC_HEAD} ...")
        await conn.exec_driver_sql(DELETE_ALL_SQL)
        await conn.exec_driver_sql(INSERT_SQL_TEMPLATE.format(ALEMBIC_HEAD))

    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
