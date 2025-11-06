# app/api/v1/employees_router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import get_current_user
from app.models.employee import Employee
from app.models.org_unit import OrgUnit
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
    get_employee_with_refs,
    apply_self_update,
    apply_admin_update,
)
from app.schemas.common import ErrorResponse, ErrorCode

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
    dependencies=[Depends(get_current_user)],
)

async def _build_employee_detail(employee: Employee) -> EmployeeDetail:
    # менеджер (уже подгружен через selectinload)
    manager_obj = None
    if employee.manager:
        manager_obj = ManagerInfo(
            id=employee.manager.id,
            first_name=employee.manager.first_name,
            last_name=employee.manager.last_name,
            title=employee.manager.title,
        )

    # орг-юнит (уже подгружен)
    org_unit_obj = None
    if employee.lowest_org_unit:
        org_unit_obj = OrgUnitInfo(
            id=employee.lowest_org_unit.id,
            name=employee.lowest_org_unit.name,
            unit_type=employee.lowest_org_unit.unit_type,
        )

    return EmployeeDetail(
        id=employee.id,
        email=employee.email,
        first_name=employee.first_name,
        middle_name=employee.middle_name,
        last_name=employee.last_name,
        title=employee.title,
        status=employee.status,
        work_city=employee.work_city,
        work_format=employee.work_format,
        time_zone=employee.time_zone,
        bio=employee.bio,
        hire_date=employee.hire_date,
        is_admin=bool(employee.is_admin),
        is_blocked=bool(employee.is_blocked),
        last_login_at=employee.last_login_at,
        manager=manager_obj,
        org_unit=org_unit_obj,
    )


# ---------------------------------------------------------------------------
# Список сотрудников (краткая информация)
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[EmployeePublic])
async def list_employees(session: AsyncSession = Depends(get_async_session)):
    try:
        employees = await get_all_employees(session)
        return [
            {
                "id": e.id,
                "first_name": e.first_name,
                "middle_name": e.middle_name,   # добавили для симметрии со схемой
                "last_name": e.last_name,
                "email": e.email,
                "title": e.title,
                "status": e.status,
            }
            for e in employees
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.single(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Unexpected error: {e}",
                status=500,
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# Подробная карточка сотрудника
# ---------------------------------------------------------------------------
@router.get("/{employee_id}", response_model=EmployeeDetail)
async def get_employee(
    employee_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    employee = await get_employee_with_refs(session, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message="Employee not found",
                status=404,
            ).model_dump(),
        )
    return await _build_employee_detail(employee)


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
        await session.refresh(current_user)
    return await _build_employee_detail(current_user)


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

    # грузим с отношениями, чтобы вернуть полную карточку после обновления
    target = await get_employee_with_refs(session, employee_id)
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
        await session.refresh(target)

    return await _build_employee_detail(target)