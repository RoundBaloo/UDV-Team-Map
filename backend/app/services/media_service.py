from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.services.storage_service import delete_object, object_public_url


async def delete_media_and_object_by_id(
    session: AsyncSession,
    media_id: int,
) -> bool:
    """Удаляет объект из бакета и запись media по id.

    Возвращает:
      - True, если media найдена и объект в бакете успешно удалён,
      - False, если media не найдена или удаление из бакета не удалось.
    """
    media = (
        await session.execute(
            select(Media).where(Media.id == media_id),
        )
    ).scalar_one_or_none()

    if not media:
        return False

    try:
        await delete_object(media.storage_key)
    except Exception:  # noqa: BLE001
        return False

    await session.delete(media)
    return True


async def resolve_media_public_url(
    session: AsyncSession,
    media_id: int,
) -> str | None:
    """Возвращает public_url по media_id или None, если записи нет."""
    if not media_id:
        return None

    row = await session.execute(
        select(Media.storage_key).where(Media.id == media_id),
    )
    storage_key = row.scalar_one_or_none()
    if not storage_key:
        return None

    return object_public_url(storage_key)
