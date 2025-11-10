from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_async_session
from app.utils.encoding import validate_utf8_or_raise

from app.services.org_unit_service import build_org_tree
from app.services.media_service import resolve_media_public_url
from app.services.employee_service import search_employees

from app.schemas.org_structure import OrgNode
from app.schemas.employee import EmployeeDetail, ManagerInfo, OrgUnitInfo
from app.schemas.media import MediaInfo
from app.schemas.common import ErrorResponse, ErrorCode

from app.models.employee import Employee

router = APIRouter(
    prefix="/org-units",
    tags=["OrgUnits"],
    dependencies=[Depends(get_current_user)],
)

@router.get("/", response_model=OrgNode)
async def get_org_structure(
    session: AsyncSession = Depends(get_async_session),
):
    try:
        return await build_org_tree(session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{org_unit_id}/employees", response_model=List[EmployeeDetail])
async def list_unit_employees(
    org_unit_id: int = Path(..., gt=0),
    q: str | None = Query(None, description="Поисковая строка; если пусто — просто список юнита"),
    session: AsyncSession = Depends(get_async_session),
    _: Employee = Depends(get_current_user),
):
    async def _to_detail(e: Employee) -> EmployeeDetail:
        manager_obj = None
        if e.manager:
            manager_obj = ManagerInfo(
                id=e.manager.id,
                first_name=e.manager.first_name,
                last_name=e.manager.last_name,
                title=e.manager.title,
            )

        org_unit_obj = None
        if e.lowest_org_unit:
            org_unit_obj = OrgUnitInfo(
                id=e.lowest_org_unit.id,
                name=e.lowest_org_unit.name,
                unit_type=e.lowest_org_unit.unit_type,
            )

        photo_obj = None
        if e.photo_id:
            url = await resolve_media_public_url(session, e.photo_id)
            if url:
                photo_obj = MediaInfo(id=e.photo_id, public_url=url)

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
        # 1) получаем список найденных (в правильном порядке по рангу/похожести)
        employees = await search_employees(session=session, q=q, org_unit_id=org_unit_id)
        ids = [e.id for e in employees]
        if not ids:
            return []

        # 2) рефетчим полные сущности одним запросом с eager-загрузкой связей
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.employee import Employee

        full_rows = await session.execute(
            select(Employee)
            .where(Employee.id.in_(ids))
            .options(
                selectinload(Employee.manager),
                selectinload(Employee.lowest_org_unit),
            )
        )
        by_id = {e.id: e for e in full_rows.scalars().all()}

        # 3) собираем ответ строго в исходном порядке ids (сохраняем сортировку поиска)
        items: list[EmployeeDetail] = []
        for eid in ids:
            e = by_id.get(eid)
            if e is not None:
                items.append(await _to_detail(e))
        return items
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.single(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Unexpected error: {ex}",
                status=500,
            ).model_dump(),
        )