from __future__ import annotations

"""CLI-скрипт для запуска синхронизации сотрудников."""

import asyncio
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from app.db.session import async_session_maker  # noqa: E402
from app.services.sync.runner import run_employee_sync  # noqa: E402


async def main() -> None:
    async with async_session_maker() as session:
        summary = await run_employee_sync(
            session=session,
            trigger="manual",
        )
    print(f"Sync finished. Summary: {summary}")


if __name__ == "__main__":
    asyncio.run(main())
