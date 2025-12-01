from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.db.session import get_async_session
from app.models.employee import Employee
from app.schemas.common import ErrorCode, ErrorResponse
from app.schemas.employee import (
    EmployeeAdminUpdate,
    EmployeeDetail,
    EmployeeSelfUpdate,
    ManagerInfo,
    OrgUnitInfo,
    SkillOption,
    TitleItem,
)
from app.schemas.media import MediaInfo
from app.services.employee_service import (
    apply_admin_update,
    apply_self_update,
    search_employees,
    search_skill_names,
    search_titles,
)
from app.services.media_service import resolve_media_public_url
from app.utils.encoding import validate_utf8_or_raise

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
    dependencies=[Depends(get_current_user)],
)


async def _build_employee_detail_by_id(
    employee_id: int,
    session: AsyncSession,
) -> EmployeeDetail:
    """Формирует детализированную карточку сотрудника по идентификатору.

    Args:
        employee_id: Идентификатор сотрудника.
        session: Асинхронная сессия базы данных.

    Returns:
        Детализированная информация о сотруднике.
    """
    db_emp = (
        await session.execute(
            select(Employee)
            .where(Employee.id == employee_id)
            .options(
                selectinload(Employee.manager),
                selectinload(Employee.department),
                selectinload(Employee.direction),
            ),
        )
    ).scalar_one_or_none()

    if db_emp is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message="Сотрудник не найден",
                status=404,
            ).model_dump(),
        )

    manager_obj: ManagerInfo | None = None
    if db_emp.manager:
        manager_obj = ManagerInfo(
            id=db_emp.manager.id,
            first_name=db_emp.manager.first_name,
            last_name=db_emp.manager.last_name,
            title=db_emp.manager.title,
        )

    org_unit_obj: OrgUnitInfo | None = None
    lowest_unit = db_emp.direction or db_emp.department
    if lowest_unit:
        org_unit_obj = OrgUnitInfo(
            id=lowest_unit.id,
            name=lowest_unit.name,
            unit_type=lowest_unit.unit_type,
        )

    photo_obj: MediaInfo | None = None
    pid = getattr(db_emp, "photo_id", None)
    if pid:
        url = await resolve_media_public_url(session, pid)
        if url:
            photo_obj = MediaInfo(id=pid, public_url=url)

    return EmployeeDetail(
        id=db_emp.id,
        email=db_emp.email,
        first_name=db_emp.first_name,
        middle_name=db_emp.middle_name,
        last_name=db_emp.last_name,
        title=db_emp.title,
        status=db_emp.status,
        work_city=db_emp.work_city,
        work_format=db_emp.work_format,
        time_zone=db_emp.time_zone,
        work_phone=db_emp.work_phone,
        mattermost_handle=db_emp.mattermost_handle,
        telegram_handle=db_emp.telegram_handle,
        birth_date=db_emp.birth_date,
        hire_date=db_emp.hire_date,
        bio=db_emp.bio,
        skill_ratings=db_emp.skill_ratings,
        is_admin=bool(db_emp.is_admin),
        is_blocked=bool(db_emp.is_blocked),
        last_login_at=db_emp.last_login_at,
        photo=photo_obj,
        manager=manager_obj,
        org_unit=org_unit_obj,
    )


def _parse_skill_filters(raw_skills: list[str] | None) -> dict[str, int] | None:
    """Парсит query-параметр навыков в словарь {name: level}.

    Формат элемента списка: "<skill_name>:<level>", где:
    * skill_name — строка;
    * level — int в диапазоне 1..5.

    Используются не более трёх навыков.
    Некорректный ввод игнорируется.

    Args:
        raw_skills: Список строковых представлений навыков и уровней.

    Returns:
        Словарь вида {название_навыка: уровень} или None.
    """
    if not raw_skills:
        return None

    result: dict[str, int] = {}
    for item in raw_skills:
        if not item:
            continue

        if ":" not in item:
            continue

        name_part, level_part = item.split(":", 1)
        name = name_part.strip()
        if not name:
            continue

        try:
            level = int(level_part)
        except ValueError:
            continue

        if level < 1 or level > 5:
            continue

        result[name] = level
        if len(result) >= 3:
            break

    return result or None


@router.get("/me", response_model=EmployeeDetail)
async def get_me(
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
) -> EmployeeDetail:
    """Возвращает детальную карточку текущего пользователя.

    Args:
        session: Асинхронная сессия базы данных.
        current_user: Текущий аутентифицированный пользователь.

    Returns:
        Детализированная информация о текущем пользователе.
    """
    return await _build_employee_detail_by_id(current_user.id, session)


@router.get("/", response_model=list[EmployeeDetail])
async def list_employees(
    q: str | None = Query(
        None,
        description=(
            "Поисковая строка (UTF-8 percent-encoded); "
            "если пусто — возвращается список сотрудников."
        ),
    ),
    skills: list[str] | None = Query(
        default=None,
        description=(
            "Фильтр по навыкам, формат элемента: 'skill_name:level'. "
            "Можно передать до 3 значений. Совпадение по точному уровню."
        ),
    ),
    titles: list[str] | None = Query(
        default=None,
        description="Фильтр по должностям: список полных названий должности.",
    ),
    legal_entity_ids: list[int] | None = Query(
        default=None,
        description=(
            "Фильтр по юр. лицам (unit_type='legal_entity'): "
            "список org_unit_id, под которыми должен лежать сотрудник."
        ),
    ),
    session: AsyncSession = Depends(get_async_session),
) -> list[EmployeeDetail]:
    """Возвращает список сотрудников с поиском и фильтрами.

    Args:
        q: Поисковая строка для полнотекстового поиска.
        skills: Фильтр по навыкам в формате 'skill_name:level'.
        titles: Фильтр по полным названиям должностей.
        legal_entity_ids: Список идентификаторов юрлиц для фильтрации.
        session: Асинхронная сессия базы данных.

    Returns:
        Список детализированных карточек сотрудников.
    """
    validate_utf8_or_raise(q)

    skill_filters = _parse_skill_filters(skills)

    rows = await search_employees(
        session=session,
        q=q,
        org_unit_id=None,
        skill_filters=skill_filters,
        titles=titles or None,
        legal_entity_ids=legal_entity_ids or None,
    )
    ids = [e.id for e in rows]
    items = await asyncio.gather(
        *(_build_employee_detail_by_id(eid, session) for eid in ids),
    )
    return list(items)


@router.get("/skills/search", response_model=list[SkillOption])
async def search_skills_endpoint(
    q: str | None = Query(
        default=None,
        description=(
            "Поиск по названию навыка (префикс). "
            "Если не задан — возвращаются все уникальные навыки "
            "(в разумных пределах)."
        ),
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Максимальное количество навыков в ответе.",
    ),
    session: AsyncSession = Depends(get_async_session),
) -> list[SkillOption]:
    """Поиск по доступным навыкам (для автодополнения в фильтре).

    Args:
        q: Поисковая строка для поиска по названию навыка (префикс).
        limit: Максимальное количество элементов в ответе.
        session: Асинхронная сессия базы данных.

    Returns:
        Список доступных вариантов навыков.
    """
    validate_utf8_or_raise(q)

    try:
        names = await search_skill_names(
            session=session,
            q=q,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.single(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Неожиданная ошибка: {exc}",
                status=500,
            ).model_dump(),
        ) from exc

    return [SkillOption(name=name) for name in names]


@router.get("/titles/search", response_model=list[TitleItem])
async def search_titles_endpoint(
    q: str | None = Query(
        default=None,
        description=(
            "Поиск по названию должности (префикс). "
            "Если не задан — возвращаются все уникальные должности "
            "(в разумных пределах)."
        ),
    ),
    limit: int = Query(
        30,
        ge=1,
        le=200,
        description="Максимальное количество должностей в ответе.",
    ),
    session: AsyncSession = Depends(get_async_session),
) -> list[TitleItem]:
    """Поиск по должностям (для автодополнения в фильтре).

    Args:
        q: Поисковая строка для поиска по названию должности (префикс).
        limit: Максимальное количество элементов в ответе.
        session: Асинхронная сессия базы данных.

    Returns:
        Список доступных вариантов должностей.
    """
    validate_utf8_or_raise(q)

    try:
        names = await search_titles(
            session=session,
            q=q,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.single(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Неожиданная ошибка: {exc}",
                status=500,
            ).model_dump(),
        ) from exc

    return [TitleItem(title=name) for name in names]


@router.get("/{employee_id}", response_model=EmployeeDetail)
async def get_employee(
    employee_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> EmployeeDetail:
    """Возвращает детальную карточку сотрудника по идентификатору.

    Args:
        employee_id: Идентификатор сотрудника.
        session: Асинхронная сессия базы данных.

    Returns:
        Детализированная информация о сотруднике.
    """
    return await _build_employee_detail_by_id(employee_id, session)


@router.patch("/me", response_model=EmployeeDetail)
async def update_me(
    payload: EmployeeSelfUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
) -> EmployeeDetail:
    """Обновляет данные текущего пользователя.

    Args:
        payload: Данные для частичного обновления профиля.
        session: Асинхронная сессия базы данных.
        current_user: Текущий аутентифицированный пользователь.

    Returns:
        Обновлённая детальная карточка пользователя.
    """
    changed = await apply_self_update(
        session,
        current_user,
        payload.model_dump(exclude_unset=True),
    )
    if changed:
        await session.commit()

    return await _build_employee_detail_by_id(current_user.id, session)


@router.patch("/{employee_id}", response_model=EmployeeDetail)
async def admin_update_employee(
    employee_id: int,
    payload: EmployeeAdminUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
) -> EmployeeDetail:
    """Обновляет данные сотрудника от имени администратора.

    Args:
        employee_id: Идентификатор сотрудника.
        payload: Данные для частичного обновления профиля.
        session: Асинхронная сессия базы данных.
        current_user: Текущий аутентифицированный пользователь.

    Returns:
        Обновлённая детальная карточка сотрудника.

    Raises:
        HTTPException: Если у текущего пользователя нет прав администратора
            или сотрудник не найден.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_FORBIDDEN,
                message="Требуются права администратора",
                status=403,
            ).model_dump(),
        )

    target = (
        await session.execute(
            select(Employee).where(Employee.id == employee_id),
        )
    ).scalar_one_or_none()
    if target is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message="Сотрудник не найден",
                status=404,
            ).model_dump(),
        )

    changed = await apply_admin_update(
        session,
        target,
        payload.model_dump(exclude_unset=True),
    )
    if changed:
        await session.commit()

    return await _build_employee_detail_by_id(employee_id, session)
