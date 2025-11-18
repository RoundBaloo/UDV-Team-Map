from __future__ import annotations

"""
Временный служебный скрипт.

Назначение:
- локально запускать синхронизацию сотрудников из JSON-файлов
  (тестовые данные вместо подключения к реальному источнику AD).
Удобен для отладки и прогона sync-логики в дев/тест-среде.
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from app.db.session import async_session_maker
from app.services.sync.runner import run_employee_sync


async def run_one(json_path: Path) -> Dict[str, int]:
    """Запускает синхронизацию для одного JSON-файла и возвращает summary."""
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    payload: Any = json.loads(json_path.read_text(encoding="utf-8"))

    async with async_session_maker() as session:
        summary = await run_employee_sync(
            session,
            payload=payload,
            trigger="manual",
        )
        return summary


async def main() -> None:
    """Парсит аргументы CLI и последовательно запускает sync по указанным файлам."""
    parser = argparse.ArgumentParser(
        description="Run employee sync from JSON test files",
    )
    parser.add_argument(
        "-f",
        "--file",
        dest="files",
        action="append",
        help="Path to JSON file (you can repeat the flag for multiple files)",
    )
    args = parser.parse_args()

    if args.files:
        files: List[Path] = [Path(p).resolve() for p in args.files]
    else:
        files = [Path("data_source/source_v1.json").resolve()]

    for p in files:
        print(f"\n=== Running sync for: {p} ===")
        try:
            summary = await run_one(p)
            print("Sync summary:")
            print(f"  - created:   {summary.get('created', 0)}")
            print(f"  - updated:   {summary.get('updated', 0)}")
            print(f"  - orphaned:  {summary.get('orphaned', 0)}")
            print(f"  - errors:    {summary.get('errors', 0)}")
        except Exception as e:
            print(f"Sync failed for {p.name}: {e}")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
