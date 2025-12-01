from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.db.session import get_async_session
from app.models.employee import Employee
from app.models.org_unit import OrgUnit
from app.schemas.common import ErrorCode, ErrorResponse
from app.schemas.employee import EmployeeDetail, ManagerInfo, OrgUnitInfo
from app.schemas.media import MediaInfo
from app.schemas.org_structure import (
    DomainItem,
    LegalEntityItem,
    OrgNode,
    OrgUnitSearchItem,
)
from app.services.employee_service import search_employees
from app.services.media_service import resolve_media_public_url
from app.services.org_unit_service import (
    build_org_tree,
    list_domains,
    search_legal_entities,
    search_org_units,
)
from app.utils.encoding import validate_utf8_or_raise

router = APIRouter(
    prefix="/org-units",
    tags=["OrgUnits"],
    dependencies=[Depends(get_current_user)],
)


async def _validate_org_unit_ids_of_type(
    session: AsyncSession,
    ids: list[int] | None,
    *,
    expected_type: str,
    field_name: str,
) -> None:
    """Проверяет, что все org_unit_id существуют и имеют нужный тип.

    Args:
        session: Асинхронная сессия базы данных.
        ids: Список идентификаторов орг-юнитов для проверки.
        expected_type: Ожидаемый unit_type для всех элементов.
        field_name: Имя поля фильтра для сообщений об ошибке.

    Raises:
        HTTPException: Если часть идентификаторов отсутствует или имеет
            некорректный тип.
    """
    if not ids:
        return

    unique_ids = sorted(set(ids))

    res = await session.execute(
        select(OrgUnit.id, OrgUnit.unit_type).where(OrgUnit.id.in_(unique_ids)),
    )
    rows = res.all()
    by_id = {row[0]: row[1] for row in rows}

    missing = [oid for oid in unique_ids if oid not in by_id]
    wrong_type = [oid for oid, utype in by_id.items() if utype != expected_type]

    if not missing and not wrong_type:
        return

    parts: list[str] = []
    if missing:
        parts.append(
            "не найдены org_unit с id: " + ", ".join(map(str, missing)),
        )
    if wrong_type:
        parts.append(
            f"для фильтра '{field_name}' ожидаются org_unit с "
            f"unit_type='{expected_type}', но для id: "
            f"{', '.join(map(str, wrong_type))} тип другой",
        )

    message = (
        f"Некорректные значения фильтра '{field_name}': " + "; ".join(parts)
    )

    raise HTTPException(
        status_code=400,
        detail=ErrorResponse.single(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status=400,
        ).model_dump(),
    )


@router.get("/", response_model=OrgNode)
async def get_org_structure(
    session: AsyncSession = Depends(get_async_session),
) -> OrgNode:
    """Возвращает дерево оргструктуры.

    Args:
        session: Асинхронная сессия базы данных.

    Returns:
        Корневой узел дерева оргструктуры.

    Raises:
        HTTPException: Если дерево оргструктуры не найдено или некорректно.
    """
    try:
        return await build_org_tree(session)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.get(
    "/search",
    response_model=list[OrgUnitSearchItem],
    summary="Поиск по орг-юнитам",
)
async def search_org_units_endpoint(
    q: str | None = Query(
        default=None,
        description=(
            "Поисковая строка по названию орг-юнита. "
            "Если не задана — возвращаем все подходящие узлы."
        ),
    ),
    domain_ids: list[int] | None = Query(
        default=None,
        description=(
            "Фильтр по доменам: список org_unit_id с unit_type='domain'. "
            "Возвращаем только те узлы, у которых в path есть хотя бы один "
            "из указанных доменов."
        ),
    ),
    legal_entity_ids: list[int] | None = Query(
        default=None,
        description=(
            "Фильтр по юр. лицам: список org_unit_id "
            "с unit_type='legal_entity'. "
            "Возвращаем только те узлы, у которых в path есть хотя бы одно "
            "из указанных юр. лиц."
        ),
    ),
    session: AsyncSession = Depends(get_async_session),
) -> list[OrgUnitSearchItem]:
    """Ищет орг-юниты с фильтрами по доменам и юрлицам.

    Args:
        q: Поисковая строка по названию орг-юнита.
        domain_ids: Список идентификаторов доменов для фильтрации.
        legal_entity_ids: Список идентификаторов юрлиц для фильтрации.
        session: Асинхронная сессия базы данных.

    Returns:
        Список найденных орг-юнитов.

    Raises:
        HTTPException: При ошибке валидации фильтров или внутренней ошибке.
    """
    validate_utf8_or_raise(q)

    await _validate_org_unit_ids_of_type(
        session,
        domain_ids,
        expected_type="domain",
        field_name="domain_ids",
    )
    await _validate_org_unit_ids_of_type(
        session,
        legal_entity_ids,
        expected_type="legal_entity",
        field_name="legal_entity_ids",
    )

    try:
        return await search_org_units(
            session=session,
            q=q,
            domain_ids=domain_ids or None,
            legal_entity_ids=legal_entity_ids or None,
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


@router.get(
    "/domains",
    response_model=list[DomainItem],
    summary="Список доменов",
)
async def list_domains_endpoint(
    session: AsyncSession = Depends(get_async_session),
) -> list[DomainItem]:
    """Возвращает полный список доменов.

    Args:
        session: Асинхронная сессия базы данных.

    Returns:
        Список доменов (unit_type='domain').

    Raises:
        HTTPException: При внутренней ошибке сервера.
    """
    try:
        entities = await list_domains(session=session)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.single(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Неожиданная ошибка: {exc}",
                status=500,
            ).model_dump(),
        ) from exc

    return [
        DomainItem(
            id=ou.id,
            name=ou.name,
        )
        for ou in entities
    ]


@router.get(
    "/legal-entities/search",
    response_model=list[LegalEntityItem],
    summary="Поиск по юр. лицам",
)
async def search_legal_entities_endpoint(
    q: str | None = Query(
        default=None,
        description=(
            "Поиск по названию юр. лица (unit_type='legal_entity'). "
            "Если не задан — возвращаем все активные юр. лица "
            "(с учётом фильтра по домену, если он указан)."
        ),
    ),
    domain_id: int | None = Query(
        default=None,
        description=(
            "Опциональный фильтр по домену: org_unit_id с unit_type='domain'. "
            "Если указан — возвращаем только юр. лица под этим доменом."
        ),
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Максимальное количество юр. лиц в ответе.",
    ),
    session: AsyncSession = Depends(get_async_session),
) -> list[LegalEntityItem]:
    """Возвращает список юр. лиц.

    Args:
        q: Поисковая строка по названию юр. лица.
        domain_id: Идентификатор домена для фильтрации.
        limit: Максимальное количество записей в ответе.
        session: Асинхронная сессия базы данных.

    Returns:
        Список найденных юрлиц.

    Raises:
        HTTPException: При внутренней ошибке сервера.
    """
    validate_utf8_or_raise(q)

    try:
        entities = await search_legal_entities(
            session=session,
            q=q,
            domain_id=domain_id,
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

    return [
        LegalEntityItem(
            id=ou.id,
            name=ou.name,
        )
        for ou in entities
    ]


@router.get("/{org_unit_id}/employees", response_model=list[EmployeeDetail])
async def list_unit_employees(
    org_unit_id: int = Path(
        ...,
        gt=0,
    ),
    q: str | None = Query(
        None,
        description=(
            "Поисковая строка; если пусто — "
            "возвращается список сотрудников юнита без фильтрации."
        ),
    ),
    session: AsyncSession = Depends(get_async_session),
    _: Employee = Depends(get_current_user),
) -> list[EmployeeDetail]:
    """Возвращает список сотрудников для указанного орг-юнита.

    Args:
        org_unit_id: Идентификатор орг-юнита.
        q: Поисковая строка для фильтрации сотрудников.
        session: Асинхронная сессия базы данных.
        _: Текущий пользователь (используется для авторизации).

    Returns:
        Список детализированных карточек сотрудников.

    Raises:
        HTTPException: При внутренней ошибке сервера.
    """

    async def _to_detail(e: Employee) -> EmployeeDetail:
        """Преобразует ORM-модель сотрудника в детальную схему.

        Args:
            e: ORM-модель сотрудника.

        Returns:
            Детализированная схема сотрудника.
        """
        manager_obj: ManagerInfo | None = None
        if e.manager:
            manager_obj = ManagerInfo(
                id=e.manager.id,
                first_name=e.manager.first_name,
                last_name=e.manager.last_name,
                title=e.manager.title,
            )

        lowest_unit = e.direction or e.department
        org_unit_obj: OrgUnitInfo | None = None
        if lowest_unit:
            org_unit_obj = OrgUnitInfo(
                id=lowest_unit.id,
                name=lowest_unit.name,
                unit_type=lowest_unit.unit_type,
            )

        photo_obj: MediaInfo | None = None
        if e.photo_id:
            url = await resolve_media_public_url(session, e.photo_id)
            if url:
                photo_obj = MediaInfo(
                    id=e.photo_id,
                    public_url=url,
                )

        return EmployeeDetail(
            id=e.id,
            email=e.email,
            first_name=e.first_name,
            middle_name=e.middle_name,
            last_name=e.last_name,
            title=e.title,
            status=e.status,
            work_city=e.work_city,
            work_format=e.work_format,
            time_zone=e.time_zone,
            work_phone=e.work_phone,
            mattermost_handle=e.mattermost_handle,
            birth_date=e.birth_date,
            hire_date=e.hire_date,
            bio=e.bio,
            skill_ratings=e.skill_ratings,
            is_admin=bool(e.is_admin),
            is_blocked=bool(e.is_blocked),
            last_login_at=e.last_login_at,
            photo=photo_obj,
            manager=manager_obj,
            org_unit=org_unit_obj,
        )

    validate_utf8_or_raise(q)

    try:
        employees = await search_employees(
            session=session,
            q=q,
            org_unit_id=org_unit_id,
        )
        ids = [e.id for e in employees]
        if not ids:
            return []

        full_rows = await session.execute(
            select(Employee)
            .where(Employee.id.in_(ids))
            .options(
                selectinload(Employee.manager),
                selectinload(Employee.department),
                selectinload(Employee.direction),
            ),
        )
        by_id = {e.id: e for e in full_rows.scalars().all()}

        items: list[EmployeeDetail] = []
        for eid in ids:
            employee = by_id.get(eid)
            if employee is not None:
                items.append(await _to_detail(employee))

        return items
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.single(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Неожиданная ошибка: {exc}",
                status=500,
            ).model_dump(),
        ) from exc
