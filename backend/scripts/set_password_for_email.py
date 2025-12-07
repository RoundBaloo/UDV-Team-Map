from __future__ import annotations

"""
Вспомогательный скрипт для dev-окружения.

Назначение:
- установить или обновить password_hash для сотрудника по email,
  чтобы можно было тестировать авторизацию до полноценной синхронизации из AD.

Использование:
  python scripts/set_password_for_email.py --email user@example.com --password Qwerty123!
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

# стараемся использовать общий хэшировщик из приложения
try:  # noqa: SIM105
    from app.core.security import get_password_hash as _app_get_password_hash  # type: ignore[import]  # noqa: E402

    def get_password_hash(password: str) -> str:
        return _app_get_password_hash(password)

except Exception:  # fallback на случай проблем с импортом в dev-сценариях
    from passlib.hash import pbkdf2_sha256  # type: ignore[import]  # noqa: E402

    def get_password_hash(password: str) -> str:
        return pbkdf2_sha256.hash(password)


async def _set_password_for_email(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> bool:
    """Обновляет password_hash для сотрудника с заданным email. Возвращает True, если пользователь найден."""
    res = await session.execute(select(Employee).where(Employee.email == email))
    emp = res.scalar_one_or_none()

    if not emp:
        print(f"❌ Employee with email {email} not found")
        return False

    emp.password_hash = get_password_hash(password)
    session.add(emp)
    await session.commit()

    print(f"✅ Password set for {email}")
    return True


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Set password for a user by email",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="User email to update",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Plain-text password to hash and store",
    )
    args = parser.parse_args()

    async with async_session_maker() as session:
        await _set_password_for_email(
            session,
            email=args.email,
            password=args.password,
        )


if __name__ == "__main__":
    asyncio.run(main())
