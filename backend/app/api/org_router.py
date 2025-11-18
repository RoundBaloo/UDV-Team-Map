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
from app.schemas.org_structure import OrgNode
from app.services.employee_service import search_employees
from app.services.media_service import resolve_media_public_url
from app.services.org_unit_service import build_org_tree
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
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


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
        # 1) получаем список найденных сотрудников
        employees = await search_employees(
            session=session,
            q=q,
            org_unit_id=org_unit_id,
        )
        ids = [e.id for e in employees]
        if not ids:
            return []

        # 2) рефетчим полные сущности одним запросом с eager-загрузкой связей
        full_rows = await session.execute(
            select(Employee)
            .where(Employee.id.in_(ids))
            .options(
                selectinload(Employee.manager),
                selectinload(Employee.lowest_org_unit),
            ),
        )
        by_id = {e.id: e for e in full_rows.scalars().all()}

        # 3) собираем ответ строго в исходном порядке ids
        items: list[EmployeeDetail] = []
        for eid in ids:
            employee = by_id.get(eid)
            if employee is not None:
                items.append(await _to_detail(employee))

        return items
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.single(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Неожиданная ошибка: {ex}",
                status=500,
            ).model_dump(),
        )
