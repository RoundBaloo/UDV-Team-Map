from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.db.session import get_async_session
from app.models.employee import Employee
from app.schemas.common import ErrorCode, ErrorResponse
from app.schemas.employee import EmployeeDetail, ManagerInfo, OrgUnitInfo
from app.schemas.media import MediaInfo
from app.schemas.org_structure import OrgNode, OrgUnitSearchItem
from app.services.employee_service import search_employees
from app.services.media_service import resolve_media_public_url
from app.services.org_unit_service import build_org_tree, search_org_units
from app.utils.encoding import validate_utf8_or_raise

router = APIRouter(
    prefix="/org-units",
    tags=["OrgUnits"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=OrgNode)
async def get_org_structure(
    session: AsyncSession = Depends(get_async_session),
) -> OrgNode:
    """Возвращает дерево оргструктуры.

    Args:
        session: Асинхронная сессия базы данных.

    Returns:
        OrgNode: Корневой узел дерева оргструктуры.

    Raises:
        HTTPException: Если дерево оргструктуры не может быть построено.
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
            "Если не задана - возвращаем все подходящие узлы."
        ),
    ),
    domain_id: int | None = Query(
        default=None,
        description=(
            "Фильтр по домену: id org_unit с unit_type='domain'. "
            "Возвращаем только те узлы, у которых в path есть этот домен."
        ),
    ),
    legal_entity_id: int | None = Query(
        default=None,
        description=(
            "Фильтр по юр. лицу: id org_unit с unit_type='legal_entity'. "
            "Возвращаем только те узлы, у которых в path есть это юр. лицо."
        ),
    ),
    session: AsyncSession = Depends(get_async_session),
) -> list[OrgUnitSearchItem]:
    """Поиск по орг-юнитам с поддержкой фильтров по домену и юр. лицу.

    Логика:

    * Если q задан:
        - используем поиск по похожести имени (unaccent + lower + trigram),
          возвращаем релевантные юниты, отсортированные по similarity и имени.
    * Если q не задан:
        - возвращаем все подходящие орг-юниты (без LIMIT, как ты хотел).

    Фильтры domain_id и legal_entity_id работают по path:
    если в цепочке от корня до узла есть домен / юр. лицо с указанным id,
    узел попадает в выборку.
    """
    validate_utf8_or_raise(q)

    try:
        return await search_org_units(
            session=session,
            q=q,
            domain_id=domain_id,
            legal_entity_id=legal_entity_id,
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


@router.get("/{org_unit_id}/employees", response_model=list[EmployeeDetail])
async def list_unit_employees(
    org_unit_id: int = Path(
        ...,
        gt=0,
    ),
    q: str | None = Query(
        None,
        description=(
            "Поисковая строка; если пусто - возвращается "
            "список сотрудников юнита без фильтрации"
        ),
    ),
    session: AsyncSession = Depends(get_async_session),
    _: Employee = Depends(get_current_user),
) -> list[EmployeeDetail]:
    """Возвращает список сотрудников для указанного оргюнита.

    Список может быть отфильтрован по поисковой строке. Результат
    сохраняет порядок, возвращаемый поисковым сервисом.

    Args:
        org_unit_id: Идентификатор оргюнита.
        q: Поисковая строка. Если пусто, возвращается полный список юнита.
        session: Асинхронная сессия базы данных.
        _: Текущий пользователь (используется для проверки авторизации).

    Returns:
        list[EmployeeDetail]: Список детальных карточек сотрудников.

    Raises:
        HTTPException: В случае внутренних ошибок при обработке запроса.
    """

    async def _to_detail(e: Employee) -> EmployeeDetail:
        """Формирует детальную карточку сотрудника из ORM-модели."""
        manager_obj: ManagerInfo | None = None
        if e.manager:
            manager_obj = ManagerInfo(
                id=e.manager.id,
                first_name=e.manager.first_name,
                last_name=e.manager.last_name,
                title=e.manager.title,
            )

        org_unit_obj: OrgUnitInfo | None = None
        if e.lowest_org_unit:
            org_unit_obj = OrgUnitInfo(
                id=e.lowest_org_unit.id,
                name=e.lowest_org_unit.name,
                unit_type=e.lowest_org_unit.unit_type,
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
                selectinload(Employee.lowest_org_unit),
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
