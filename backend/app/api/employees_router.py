# app/api/v1/employees_router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import asyncio

from app.db.session import get_async_session
from app.core.security import get_current_user
from app.models.employee import Employee
from app.schemas.employee import (
    EmployeePublic,
    EmployeeDetail,
    ManagerInfo,
    OrgUnitInfo,
    EmployeeSelfUpdate,
    EmployeeAdminUpdate,
)
from app.services.employee_service import (
    get_all_employees,
    get_employee_with_refs,  # можно оставить для других мест, здесь не обязателен
    apply_self_update,
    apply_admin_update,
)
from app.services.media_service import resolve_media_public_url
from app.schemas.media import MediaInfo
from app.schemas.common import ErrorResponse, ErrorCode

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
    dependencies=[Depends(get_current_user)],
)

async def _build_employee_detail_by_id(employee_id: int, session: AsyncSession) -> EmployeeDetail:
    db_emp = (
        await session.execute(
            select(Employee)
            .where(Employee.id == employee_id)
            .options(
                selectinload(Employee.manager),
                selectinload(Employee.lowest_org_unit),
            )
        )
    ).scalar_one_or_none()

    if db_emp is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message="Employee not found",
                status=404,
            ).model_dump(),
        )

    manager_obj = None
    if db_emp.manager:
        manager_obj = ManagerInfo(
            id=db_emp.manager.id,
            first_name=db_emp.manager.first_name,
            last_name=db_emp.manager.last_name,
            title=db_emp.manager.title,
        )

    org_unit_obj = None
    if db_emp.lowest_org_unit:
        org_unit_obj = OrgUnitInfo(
            id=db_emp.lowest_org_unit.id,
            name=db_emp.lowest_org_unit.name,
            unit_type=db_emp.lowest_org_unit.unit_type,
        )

    photo_obj = None
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

@router.get("/me", response_model=EmployeeDetail)
async def get_me(
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    return await _build_employee_detail_by_id(current_user.id, session)

# ---------------------------------------------------------------------------
# Список сотрудников (полные карточки)
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[EmployeeDetail])
async def list_employees(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Employee.id)
        .where(Employee.status == "active")
        .order_by(Employee.last_name.asc(), Employee.first_name.asc())
    )
    ids = [row[0] for row in result.all()]
    # Параллельно собираем полные карточки
    items = await asyncio.gather(*[
        _build_employee_detail_by_id(eid, session) for eid in ids
    ])
    return items

# ---------------------------------------------------------------------------
# Подробная карточка сотрудника
# ---------------------------------------------------------------------------
@router.get("/{employee_id}", response_model=EmployeeDetail)
async def get_employee(
    employee_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    return await _build_employee_detail_by_id(employee_id, session)

# ---------------------------------------------------------------------------
# PATCH /me — пользователь обновляет свои поля
# ---------------------------------------------------------------------------
@router.patch("/me", response_model=EmployeeDetail)
async def update_me(
    payload: EmployeeSelfUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    changed = await apply_self_update(session, current_user, payload.model_dump(exclude_unset=True))
    if changed:
        await session.commit()
    # важный момент: не трогаем ленивые связи current_user,
    # а делаем рефетч через билдер
    return await _build_employee_detail_by_id(current_user.id, session)

# ---------------------------------------------------------------------------
# PATCH /employees/{employee_id} — админ обновляет пользователя
# ---------------------------------------------------------------------------
@router.patch("/{employee_id}", response_model=EmployeeDetail)
async def admin_update_employee(
    employee_id: int,
    payload: EmployeeAdminUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_FORBIDDEN,
                message="Admin privileges required",
                status=403,
            ).model_dump(),
        )

    target = await (
        session.execute(
            select(Employee)
            .where(Employee.id == employee_id)
        )
    )
    target = target.scalar_one_or_none()
    if target is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message="Employee not found",
                status=404,
            ).model_dump(),
        )

    changed = await apply_admin_update(session, target, payload.model_dump(exclude_unset=True))
    if changed:
        await session.commit()

    # как и выше — рефетч с eager загрузкой
    return await _build_employee_detail_by_id(employee_id, session)
