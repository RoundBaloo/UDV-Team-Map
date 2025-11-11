from __future__ import annotations

from typing import Dict, Tuple, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
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
    DecisionPayload,
    MyModerationStatus,
)
from app.services.photo_moderation_service import (
    create_or_replace_request_for_employee,
    list_pending,
    approve,
    reject,
    get_latest_for_employee,
    NotFound, BadRequest, Conflict,
)
from app.services.media_service import resolve_media_public_url

router = APIRouter(
    prefix="/photo-moderation",
    tags=["PhotoModeration"],
    dependencies=[Depends(get_current_user)],
)


def _ensure_admin(user: Employee) -> None:
    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_FORBIDDEN,
                message="Admin privileges required",
                status=403,
            ).model_dump(),
        )


async def _fetch_employee_names(
    session: AsyncSession, employee_ids: list[int]
) -> Dict[int, Tuple[str, Optional[str], str]]:
    """Забираем имена одной пачкой: {employee_id: (first, middle, last)}."""
    if not employee_ids:
        return {}
    rows = await session.execute(
        select(Employee.id, Employee.first_name, Employee.middle_name, Employee.last_name)
        .where(Employee.id.in_(set(employee_ids)))
    )
    return {eid: (fn, mn, ln) for eid, fn, mn, ln in rows.all()}


async def _to_item(
    pm: PhotoModeration,
    session: AsyncSession,
    *,
    name_cache: Dict[int, Tuple[str, Optional[str], str]] | None = None,
) -> PhotoModerationItem:
    # Фото
    url = await resolve_media_public_url(session, pm.media_id)
    photo = MediaInfo(id=pm.media_id, public_url=url) if pm.media_id else None

    # ФИО
    if name_cache and pm.employee_id in name_cache:
        first, middle, last = name_cache[pm.employee_id]
    else:
        row = await session.execute(
            select(Employee.first_name, Employee.middle_name, Employee.last_name)
            .where(Employee.id == pm.employee_id)
        )
        first, middle, last = row.one()

    return PhotoModerationItem(
        id=pm.id,
        employee_id=pm.employee_id,
        employee_first_name=first,
        employee_middle_name=middle,
        employee_last_name=last,
        status=pm.status,
        reviewer_employee_id=pm.reviewer_employee_id,
        reviewed_at=pm.reviewed_at,
        reject_reason=pm.reject_reason,
        created_at=pm.created_at,
        photo=photo,
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


# --- Админ/HR: список pending ---
@router.get("/pending", response_model=ModerationList)
async def get_pending(
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    _ensure_admin(current_user)

    pms = await list_pending(session)  # -> list[PhotoModeration]
    emp_ids = [pm.employee_id for pm in pms]
    names = await _fetch_employee_names(session, emp_ids)  # батч

    items = [await _to_item(pm, session, name_cache=names) for pm in pms]
    return ModerationList(items=items)


# --- Админ/HR: апрув/режект ---
@router.post("/{moderation_id}/decision", response_model=PhotoModerationItem)
async def decide_request(
    moderation_id: int = Path(..., gt=0),
    payload: DecisionPayload = ...,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    _ensure_admin(current_user)
    try:
        if payload.decision == "approve":
            pm = await approve(session, moderation_id=moderation_id, reviewer_id=current_user.id)
        else:
            pm = await reject(session, moderation_id=moderation_id, reviewer_id=current_user.id, reason=payload.reason or "")
        await session.commit()
        return await _to_item(pm, session)
    except NotFound as e:
        await session.rollback()
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse.single(ErrorCode.NOT_FOUND, str(e), 404).model_dump(),
        )
    except Conflict as e:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail=ErrorResponse.single(code=ErrorCode.CONFLICT, message=str(e), status=409).model_dump(),
        )
    except BadRequest as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse.single(ErrorCode.BAD_REQUEST, str(e), 400).model_dump(),
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
