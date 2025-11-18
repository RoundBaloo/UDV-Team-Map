from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_async_session
from app.models.employee import Employee
from app.models.photo_moderation import PhotoModeration
from app.schemas.common import ErrorCode, ErrorResponse
from app.schemas.media import MediaInfo
from app.schemas.photo_moderation import (
    CreateModerationRequestMe,
    DecisionPayload,
    ModerationList,
    MyModerationStatus,
    PhotoModerationItem,
)
from app.services.media_service import resolve_media_public_url
from app.services.photo_moderation_service import (
    BadRequest,
    Conflict,
    NotFound,
    approve,
    create_or_replace_request_for_employee,
    get_latest_for_employee,
    list_pending,
    reject,
)

router = APIRouter(
    prefix="/photo-moderation",
    tags=["PhotoModeration"],
    dependencies=[Depends(get_current_user)],
)


def _ensure_admin(user: Employee) -> None:
    """Проверяет, что у пользователя есть права администратора.

    Args:
        user: Текущий пользователь.

    Raises:
        HTTPException: Если у пользователя нет прав администратора.
    """
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
    session: AsyncSession,
    employee_ids: list[int],
) -> dict[int, tuple[str, str | None, str]]:
    """Загружает ФИО сотрудников одной пачкой.

    Args:
        session: Асинхронная сессия базы данных.
        employee_ids: Список идентификаторов сотрудников.

    Returns:
        dict[int, tuple[str, str | None, str]]: Словарь вида
            {employee_id: (first_name, middle_name, last_name)}.
    """
    if not employee_ids:
        return {}

    rows = await session.execute(
        select(
            Employee.id,
            Employee.first_name,
            Employee.middle_name,
            Employee.last_name,
        ).where(
            Employee.id.in_(set(employee_ids)),
        ),
    )
    return {eid: (fn, mn, ln) for eid, fn, mn, ln in rows.all()}


async def _to_item(
    pm: PhotoModeration,
    session: AsyncSession,
    *,
    name_cache: dict[int, tuple[str, str | None, str]] | None = None,
) -> PhotoModerationItem:
    """Преобразует запись модерации фото в схему ответа.

    Args:
        pm: Запись модерации фото.
        session: Асинхронная сессия базы данных.
        name_cache: Опциональный кеш ФИО сотрудников.

    Returns:
        PhotoModerationItem: Схема с данными по модерации фото.
    """
    # Фото
    url = await resolve_media_public_url(session, pm.media_id)
    photo = MediaInfo(id=pm.media_id, public_url=url) if pm.media_id else None

    # ФИО
    if name_cache and pm.employee_id in name_cache:
        first, middle, last = name_cache[pm.employee_id]
    else:
        row = await session.execute(
            select(
                Employee.first_name,
                Employee.middle_name,
                Employee.last_name,
            ).where(
                Employee.id == pm.employee_id,
            ),
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


@router.post(
    "/requests/me",
    response_model=PhotoModerationItem,
    status_code=201,
)
async def create_my_request(
    payload: CreateModerationRequestMe,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
) -> PhotoModerationItem:
    """Создает или заменяет заявку на модерацию фото текущего пользователя.

    Args:
        payload: Данные по загруженному медиа.
        session: Асинхронная сессия базы данных.
        current_user: Текущий пользователь.

    Returns:
        PhotoModerationItem: Данные по созданной или обновленной заявке.

    Raises:
        HTTPException: Если медиа не найдено или запрос некорректен.
    """
    try:
        pm = await create_or_replace_request_for_employee(
            session,
            current_user.id,
            payload.media_id,
        )
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


@router.get(
    "/pending",
    response_model=ModerationList,
)
async def get_pending(
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
) -> ModerationList:
    """Возвращает список заявок на модерацию в статусе pending.

    Args:
        session: Асинхронная сессия базы данных.
        current_user: Текущий пользователь.

    Returns:
        ModerationList: Список заявок на модерацию.
    """
    _ensure_admin(current_user)

    pms = await list_pending(session)
    emp_ids = [pm.employee_id for pm in pms]
    names = await _fetch_employee_names(session, emp_ids)

    items = [await _to_item(pm, session, name_cache=names) for pm in pms]
    return ModerationList(items=items)


@router.post(
    "/{moderation_id}/decision",
    response_model=PhotoModerationItem,
)
async def decide_request(
    moderation_id: int = Path(..., gt=0),
    payload: DecisionPayload = ...,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
) -> PhotoModerationItem:
    """Принимает решение по заявке на модерацию фото.

    Args:
        moderation_id: Идентификатор заявки на модерацию.
        payload: Решение по заявке и дополнительные данные.
        session: Асинхронная сессия базы данных.
        current_user: Текущий пользователь.

    Returns:
        PhotoModerationItem: Обновленная заявка после принятия решения.

    Raises:
        HTTPException: Если заявка не найдена, есть конфликт
            или данные запроса некорректны.
    """
    _ensure_admin(current_user)

    try:
        if payload.decision == "approve":
            pm = await approve(
                session,
                moderation_id=moderation_id,
                reviewer_id=current_user.id,
            )
        else:
            pm = await reject(
                session,
                moderation_id=moderation_id,
                reviewer_id=current_user.id,
                reason=payload.reason or "",
            )
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
    except Conflict as e:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail=ErrorResponse.single(
                code=ErrorCode.CONFLICT,
                message=str(e),
                status=409,
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


@router.get(
    "/me/status",
    response_model=MyModerationStatus,
)
async def my_latest_status(
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
) -> MyModerationStatus:
    """Возвращает статус последней заявки на модерацию фото текущего пользователя.

    Args:
        session: Асинхронная сессия базы данных.
        current_user: Текущий пользователь.

    Returns:
        MyModerationStatus: Информация о наличии и статусе последней заявки.
    """
    pm = await get_latest_for_employee(session, current_user.id)
    return MyModerationStatus(
        has_request=pm is not None,
        last=await _to_item(pm, session) if pm else None,
    )
