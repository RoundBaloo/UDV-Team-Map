from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.media import Media
from app.services.storage_service import delete_object, object_public_url

async def delete_media_and_object_by_id(session: AsyncSession, media_id: int) -> bool:
    """
    Находит media по id, удаляет объект в бакете и (при успехе) удаляет запись из БД.
    Возвращает True, если удалили и объект, и запись; False — если media не найдено.
    Исключения из delete_object не поднимаем выше (чтобы не ронять апрув),
    но если удаление в бакете провалится — запись в БД НЕ трогаем.
    """
    media = (await session.execute(select(Media).where(Media.id == media_id))).scalar_one_or_none()
    if not media:
        return False

    try:
        await delete_object(media.storage_key)
    except Exception:
        return False

    # Бакет убрали — теперь чистим запись:
    await session.delete(media)
    return True


async def resolve_media_public_url(session: AsyncSession, media_id: int) -> str | None:
    """
    По media_id достаём storage_key и строим public_url.
    Возвращает None, если записи нет.
    """
    if not media_id:
        return None
    row = await session.execute(select(Media.storage_key).where(Media.id == media_id))
    storage_key = row.scalar_one_or_none()
    if not storage_key:
        return None
    return object_public_url(storage_key)