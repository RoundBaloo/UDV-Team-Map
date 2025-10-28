from __future__ import annotations

import asyncio
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.providers.ad_json_provider import ADJsonProvider
from app.services.sync_service import run_sync


async def run_once(path: str, label: str) -> Dict[str, Any]:
    """Сделать один прогон синхронизации с указанным JSON и показать сводку."""
    print(f">>> Running sync {label} ...")

    # провайдер читает данные из JSON
    provider = ADJsonProvider(path=path)

    # открываем сессию к БД
    async with AsyncSessionLocal() as session:
        assert isinstance(session, AsyncSession)

        # запускаем основную синхру
        result = await run_sync(
            session=session,
            provider=provider,
            trigger="manual",
        )

        # фиксируем изменения в БД
        await session.commit()

    print(f"--- Sync {label} result:")
    print(result)
    print()
    return result


async def main() -> None:
    # первый прогон: создаём всё с нуля по v1
    await run_once(
        path="data_source/source_v1.json",
        label="V1",
    )

    # второй прогон: обновления/орфаны по v2
    await run_once(
        path="data_source/source_v2.json",
        label="V2",
    )


if __name__ == "__main__":
    asyncio.run(main())
