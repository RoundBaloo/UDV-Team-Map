from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import asyncio

from app.core.security import get_current_user
from app.db.session import get_async_session

from app.services.org_unit_service import build_org_tree
from app.services.org_unit_service import get_employees_of_unit
from app.services.media_service import resolve_media_public_url

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
    session: AsyncSession = Depends(get_async_session),
    _: Employee = Depends(get_current_user),
):
    employees = await get_employees_of_unit(session, org_unit_id=org_unit_id, active_only=True)

    async def _to_detail(e: Employee) -> EmployeeDetail:
        # manager
        manager_obj = None
        if e.manager:
            manager_obj = ManagerInfo(
                id=e.manager.id,
                first_name=e.manager.first_name,
                last_name=e.manager.last_name,
                title=e.manager.title,
            )

        # org_unit
        org_unit_obj = None
        if e.lowest_org_unit:
            org_unit_obj = OrgUnitInfo(
                id=e.lowest_org_unit.id,
                name=e.lowest_org_unit.name,
                unit_type=e.lowest_org_unit.unit_type,
            )

        # photo
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

    try:
        return await asyncio.gather(*[ _to_detail(e) for e in employees ])
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.single(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Unexpected error: {ex}",
                status=500,
            ).model_dump(),
        )