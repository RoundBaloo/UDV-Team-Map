from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_async_session
from app.models.employee import Employee
from app.models.photo_moderation import PhotoModeration
from app.schemas.common import ErrorResponse, ErrorCode
from app.schemas.media import MediaInfo
from app.schemas.photo_moderation import (
    PhotoModerationItem,
    ModerationList,
    CreateModerationRequestMe,
    CreateModerationRequestAdmin,
    RejectPayload,
    MyModerationStatus,
)
from app.services.photo_moderation_service import (
    create_or_replace_request_for_employee,
    list_pending,
    approve,
    reject,
    get_latest_for_employee,
    NotFound, BadRequest,
)
from app.services.media_service import resolve_media_public_url

router = APIRouter(
    prefix="/photo-moderation",
    tags=["PhotoModeration"],
    dependencies=[Depends(get_current_user)],
)

async def _to_item(pm: PhotoModeration, session: AsyncSession) -> PhotoModerationItem:
    url = await resolve_media_public_url(session, pm.media_id)
    photo = MediaInfo(id=pm.media_id, public_url=url) if pm.media_id else None
    return PhotoModerationItem(
        id=pm.id,
        employee_id=pm.employee_id,
        status=pm.status,
        reviewer_employee_id=pm.reviewer_employee_id,
        reviewed_at=pm.reviewed_at,
        reject_reason=pm.reject_reason,
        created_at=pm.created_at,
        photo=photo,
    )

def _ensure_admin(user: Employee):
    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_FORBIDDEN,
                message="Admin privileges required",
                status=403,
            ).model_dump(),
        )

# --- Пользователь: создать/заменить заявку на модерацию своей фотки ---
@router.post("/requests/me", response_model=PhotoModerationItem, status_code=201)
async def create_my_request(
    payload: CreateModerationRequestMe,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    try:
        pm = await create_or_replace_request_for_employee(session, current_user.id, payload.media_id)
        await session.commit()
        return await _to_item(pm, session)
    except NotFound as e:
        await session.rollback()
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message=str(e),
                status=404,
            ).model_dump(),
        )
    except BadRequest as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse.single(
                code=ErrorCode.BAD_REQUEST,
                message=str(e),
                status=400,
            ).model_dump(),
        )

# --- Админ/HR: создать/заменить заявку для любого сотрудника ---
@router.post("/requests", response_model=PhotoModerationItem, status_code=201)
async def create_request_admin(
    payload: CreateModerationRequestAdmin,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    _ensure_admin(current_user)
    try:
        pm = await create_or_replace_request_for_employee(session, payload.employee_id, payload.media_id)
        await session.commit()
        return await _to_item(pm, session)
    except NotFound as e:
        await session.rollback()
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message=str(e),
                status=404,
            ).model_dump(),
        )
    except BadRequest as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse.single(
                code=ErrorCode.BAD_REQUEST,
                message=str(e),
                status=400,
            ).model_dump(),
        )

# --- Админ/HR: список pending ---
@router.get("/pending", response_model=ModerationList)
async def get_pending(
    employee_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    _ensure_admin(current_user)
    items, total = await list_pending(session, employee_id=employee_id, limit=limit, offset=offset)
    return ModerationList(
        items=[await _to_item(pm, session) for pm in items],
        total=total,
        limit=limit,
        offset=offset,
    )

# --- Админ/HR: апрув ---
@router.post("/{moderation_id}/approve", response_model=PhotoModerationItem)
async def approve_request(
    moderation_id: int = Path(..., gt=0),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    _ensure_admin(current_user)
    try:
        pm = await approve(session, moderation_id=moderation_id, reviewer_id=current_user.id)
        await session.commit()
        return await _to_item(pm, session)
    except NotFound as e:
        await session.rollback()
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message=str(e),
                status=404,
            ).model_dump(),
        )
    except BadRequest as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse.single(
                code=ErrorCode.BAD_REQUEST,
                message=str(e),
                status=400,
            ).model_dump(),
        )

# --- Админ/HR: реджект ---
@router.post("/{moderation_id}/reject", response_model=PhotoModerationItem)
async def reject_request(
    moderation_id: int = Path(..., gt=0),
    payload: RejectPayload = ...,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    _ensure_admin(current_user)
    try:
        pm = await reject(session, moderation_id=moderation_id, reviewer_id=current_user.id, reason=payload.reason)
        await session.commit()
        return await _to_item(pm, session)
    except NotFound as e:
        await session.rollback()
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message=str(e),
                status=404,
            ).model_dump(),
        )
    except BadRequest as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse.single(
                code=ErrorCode.BAD_REQUEST,
                message=str(e),
                status=400,
            ).model_dump(),
        )

# --- Пользователь: статус своей последней заявки ---
@router.get("/me/status", response_model=MyModerationStatus)
async def my_latest_status(
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    pm = await get_latest_for_employee(session, current_user.id)
    return MyModerationStatus(
        has_request=pm is not None,
        last=await _to_item(pm, session) if pm else None,
    )
