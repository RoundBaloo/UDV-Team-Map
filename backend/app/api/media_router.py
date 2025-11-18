from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_async_session
from app.models.employee import Employee
from app.models.media import Media
from app.schemas.common import ErrorCode, ErrorResponse
from app.schemas.media import (
    FinalizeUploadRequest,
    InitUploadRequest,
    InitUploadResponse,
    MediaItem,
)
from app.services.storage_service import (
    guess_ext_from_mime,
    make_storage_key,
    object_public_url,
    presign_put_url,
)

router = APIRouter(
    prefix="/media",
    tags=["Media"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/uploads/init",
    response_model=InitUploadResponse,
)
async def init_upload(
    payload: InitUploadRequest,
    _: Employee = Depends(get_current_user),
) -> InitUploadResponse:
    """Инициализирует загрузку файла в хранилище.

    Args:
        payload: Параметры загружаемого файла.
        _: Текущий пользователь (не используется в логике, нужен для авторизации).

    Returns:
        InitUploadResponse: Данные для загрузки файла и публичный URL.
    """
    ext = guess_ext_from_mime(payload.content_type)
    key = make_storage_key(ext)
    info = presign_put_url(
        key,
        content_type=payload.content_type,
        expires_seconds=900,
    )
    return InitUploadResponse(
        storage_key=info.storage_key,
        upload_url=info.presigned_url,
        public_url=info.public_url,
    )


@router.post(
    "/uploads/finalize",
    response_model=MediaItem,
    status_code=status.HTTP_201_CREATED,
)
async def finalize_upload(
    payload: FinalizeUploadRequest,
    session: AsyncSession = Depends(get_async_session),
    _: Employee = Depends(get_current_user),
) -> MediaItem:
    """Завершает загрузку файла и создает запись в таблице медиа.

    Args:
        payload: Данные о загруженном объекте хранилища.
        session: Асинхронная сессия базы данных.
        _: Текущий пользователь (не используется в логике, нужен для авторизации).

    Returns:
        MediaItem: Информация о медиа-объекте.

    Raises:
        HTTPException: Ошибка создания записи о медиа-объекте.
    """
    # Уникальность storage_key обеспечивается ограничением uq_media_storage_key
    stmt = (
        insert(Media)
        .values(storage_key=payload.storage_key)
        .returning(Media.id, Media.storage_key)
    )
    try:
        row = (await session.execute(stmt)).one()
        await session.commit()
    except Exception as e:
        await session.rollback()
        existing = (
            await session.execute(
                select(Media).where(Media.storage_key == payload.storage_key),
            )
        ).one_or_none()
        if existing:
            media_id = existing[0].id if hasattr(existing[0], "id") else existing[0]
            return MediaItem(
                id=media_id,
                storage_key=payload.storage_key,
                public_url=object_public_url(payload.storage_key),
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse.single(
                code=ErrorCode.BAD_REQUEST,
                message="Не удалось завершить загрузку файла",
                status=400,
            ).model_dump(),
        )

    media_id = row.id if hasattr(row, "id") else row[0]
    return MediaItem(
        id=media_id,
        storage_key=payload.storage_key,
        public_url=object_public_url(payload.storage_key),
    )
