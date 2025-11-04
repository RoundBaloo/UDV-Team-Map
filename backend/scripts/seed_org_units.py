# scripts/seed_org_units.py
import asyncio
import os
import sys

# чтобы работал прямой запуск: python -m scripts.seed_org_units
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.org_unit import OrgUnit


async def main():
    async with async_session_maker() as session:
        # 1) создаём юр.лицо (legal_entity)
        le = OrgUnit(name="UDV Group", unit_type="legal_entity")
        session.add(le)
        await session.flush()  # получим le.id

        # 2) создаём департаменты (department) под UDV Group
        deps = [
            OrgUnit(name="Платформа", unit_type="department", parent_id=le.id),
            OrgUnit(name="Тестирование", unit_type="department", parent_id=le.id),
            OrgUnit(name="Продукты", unit_type="department", parent_id=le.id),
        ]
        session.add_all(deps)
        await session.commit()

        # 3) выведем, что получилось
        rows = (await session.execute(
            select(OrgUnit).order_by(OrgUnit.id)
        )).scalars().all()
        print("\n=== ORG_UNITS SEEDED ===")
        for ou in rows:
            print(f"[org_unit] id={ou.id} name={ou.name!r} type={ou.unit_type!r} parent_id={ou.parent_id}")

if __name__ == "__main__":
    asyncio.run(main())
