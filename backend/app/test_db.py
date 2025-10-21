from app.db.session import engine
from sqlalchemy import text
import asyncio

async def main():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public';"))
        tables = result.scalars().all()
        print("✅ Таблицы:", tables)

asyncio.run(main())
