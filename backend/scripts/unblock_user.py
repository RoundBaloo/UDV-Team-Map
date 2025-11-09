from __future__ import annotations

import asyncio
import os
import sys
import argparse

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.employee import Employee


async def main() -> None:
    parser = argparse.ArgumentParser(description="Unset is_blocked for a user by id")
    parser.add_argument("--id", type=int, required=True, help="Employee id")
    parser.add_argument(
        "--value",
        choices=["true", "false"],
        default="false",
        help="Set is_blocked to true/false (default: false)",
    )
    args = parser.parse_args()
    new_value = args.value.lower() == "true"

    async with async_session_maker() as session:
        res = await session.execute(select(Employee).where(Employee.id == args.id))
        user = res.scalar_one_or_none()
        if not user:
            print(f"❌ Employee id={args.id} not found")
            return

        user.is_blocked = new_value
        session.add(user)
        await session.commit()
        print(f"✅ id={user.id}: is_blocked set to {user.is_blocked}")

if __name__ == "__main__":
    asyncio.run(main())
