from __future__ import annotations

"""
Вспомогательный dev-скрипт.

Назначение:
- быстро установить флаг is_blocked для сотрудника по id,
  например, если единственный админ оказался заблокирован.

Пример использования:
  python scripts/set_block_flag.py --id 1 --value false
"""

import argparse
import asyncio
import os
import sys

# чтобы импорты app.* работали при запуске из scripts/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # noqa: E402

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db.session import async_session_maker  # noqa: E402
from app.models.employee import Employee  # noqa: E402


async def _set_block_flag(
    session: AsyncSession,
    *,
    employee_id: int,
    is_blocked: bool,
) -> bool:
    """
    Устанавливает флаг is_blocked для сотрудника.
    Возвращает True, если пользователь найден.
    """
    res = await session.execute(
        select(Employee).where(Employee.id == employee_id),
    )
    user = res.scalar_one_or_none()

    if not user:
        print(f"❌ Employee id={employee_id} not found")
        return False

    user.is_blocked = is_blocked
    session.add(user)
    await session.commit()

    print(f"✅ id={user.id}: is_blocked set to {user.is_blocked}")
    return True


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Set is_blocked flag for a user by id",
    )
    parser.add_argument(
        "--id",
        type=int,
        required=True,
        help="Employee id",
    )
    parser.add_argument(
        "--value",
        choices=["true", "false"],
        default="false",
        help="Set is_blocked to true/false (default: false)",
    )
    args = parser.parse_args()
    new_value = args.value.lower() == "true"

    async with async_session_maker() as session:
        await _set_block_flag(
            session,
            employee_id=args.id,
            is_blocked=new_value,
        )


if __name__ == "__main__":
    asyncio.run(main())
