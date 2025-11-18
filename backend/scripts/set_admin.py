from __future__ import annotations

"""
Вспомогательный скрипт для dev-окружения.

Назначение:
- установить или снять флаг is_admin у сотрудника по email.
Использование:
  python scripts/set_admin.py --email user@example.com --value true
"""

import argparse
import asyncio
import os
import sys

# чтобы импорты app.* работали при запуске из scripts/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.employee import Employee


async def _set_admin_flag(
    session: AsyncSession,
    *,
    email: str,
    is_admin: bool,
) -> bool:
    """Устанавливает is_admin для сотрудника с заданным email. Возвращает True, если пользователь найден."""
    res = await session.execute(select(Employee).where(Employee.email == email))
    user = res.scalar_one_or_none()

    if not user:
        print(f"❌ Employee with email {email} not found")
        return False

    user.is_admin = is_admin
    session.add(user)
    await session.commit()

    print(f"✅ {email}: is_admin set to {user.is_admin} (id={user.id})")
    return True


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Set is_admin flag for a user by email",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="User email to promote/demote",
    )
    parser.add_argument(
        "--value",
        choices=["true", "false"],
        default="true",
        help="Set is_admin to true/false (default: true)",
    )
    args = parser.parse_args()

    make_admin = args.value.lower() == "true"

    async with async_session_maker() as session:
        await _set_admin_flag(session, email=args.email, is_admin=make_admin)


if __name__ == "__main__":
    asyncio.run(main())
