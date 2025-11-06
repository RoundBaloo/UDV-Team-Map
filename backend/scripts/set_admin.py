# scripts/set_admin.py
from __future__ import annotations

import asyncio
import os
import sys
import argparse

# чтобы импорты app.* работали при запуске из scripts/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.employee import Employee


async def main() -> None:
    parser = argparse.ArgumentParser(description="Set is_admin flag for a user by email")
    parser.add_argument("--email", required=True, help="User email to promote")
    parser.add_argument("--value", choices=["true", "false"], default="true",
                        help="Set is_admin to true/false (default: true)")
    args = parser.parse_args()

    make_admin = args.value.lower() == "true"

    async with async_session_maker() as session:
        res = await session.execute(select(Employee).where(Employee.email == args.email))
        user = res.scalar_one_or_none()

        if not user:
            print(f"❌ Employee with email {args.email} not found")
            return

        user.is_admin = make_admin
        session.add(user)
        await session.commit()

        print(f"✅ {args.email}: is_admin set to {user.is_admin} (id={user.id})")


if __name__ == "__main__":
    asyncio.run(main())
