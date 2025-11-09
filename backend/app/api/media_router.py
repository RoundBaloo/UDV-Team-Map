# app/api/v1/media_router.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_async_session
from app.models.employee import Employee
from app.models.media import Media
from app.schemas.common import ErrorResponse, ErrorCode
from app.schemas.media import (
    InitUploadRequest, InitUploadResponse,
    FinalizeUploadRequest, MediaItem
)
from app.services.storage_service import (
    presign_put_url, make_storage_key, object_public_url, guess_ext_from_mime
)

router = APIRouter(
    prefix="/media",
    tags=["Media"],
    dependencies=[Depends(get_current_user)],
)

@router.post("/uploads/init", response_model=InitUploadResponse)
async def init_upload(
    payload: InitUploadRequest,
    _: Employee = Depends(get_current_user),
):
    ext = guess_ext_from_mime(payload.content_type)
    key = make_storage_key(ext)
    info = presign_put_url(key, content_type=payload.content_type, expires_seconds=900)
    return InitUploadResponse(
        storage_key=info.storage_key,
        upload_url=info.presigned_url,
        public_url=info.public_url,
    )

@router.post("/uploads/finalize", response_model=MediaItem, status_code=201)
async def finalize_upload(
    payload: FinalizeUploadRequest,
    session: AsyncSession = Depends(get_async_session),
    _: Employee = Depends(get_current_user),
):
    # гарантируем уникальность storage_key через uq_media_storage_key
    stmt = insert(Media).values(storage_key=payload.storage_key).returning(Media.id, Media.storage_key)
    try:
        row = (await session.execute(stmt)).one()
        await session.commit()
    except Exception as e:
        await session.rollback()
        # возможно, уже существует?
        existing = (await session.execute(select(Media).where(Media.storage_key == payload.storage_key))).one_or_none()
        if existing:
            media_id = existing[0].id if hasattr(existing[0], "id") else existing[0]
            return MediaItem(id=media_id, storage_key=payload.storage_key, public_url=object_public_url(payload.storage_key))
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse.single(
                code=ErrorCode.BAD_REQUEST,
                message=f"Failed to finalize upload: {e}",
                status=400,
            ).model_dump(),
        )

    media_id = row.id if hasattr(row, "id") else row[0]
    return MediaItem(id=media_id, storage_key=payload.storage_key, public_url=object_public_url(payload.storage_key))
