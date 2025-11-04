# scripts/set_password_for_email.py
import asyncio
import os
import sys
import argparse

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.employee import Employee

# стараемся использовать общий хэшировщик из приложения
try:
    from app.core.security import get_password_hash
except Exception:
    # аварийный fallback — pbkdf2 (без нативных зависимостей)
    from passlib.hash import pbkdf2_sha256
    def get_password_hash(p: str) -> str:
        return pbkdf2_sha256.hash(p)

async def main():
    parser = argparse.ArgumentParser(description="Set password for user by email")
    parser.add_argument("--email", required=False, default="ivan.petrov@example.com")
    parser.add_argument("--password", required=False, default="Test1234!")
    args = parser.parse_args()

    async with async_session_maker() as session:
        emp = (await session.execute(select(Employee).where(Employee.email == args.email))).scalar_one_or_none()
        if not emp:
            print(f"❌ Employee with email {args.email} not found")
            return

        emp.password_hash = get_password_hash(args.password)
        await session.commit()
        print(f"✅ Password set for {args.email}")

if __name__ == "__main__":
    asyncio.run(main())
