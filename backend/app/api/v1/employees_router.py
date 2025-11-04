# app/api/v1/employees_router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
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
)
from app.schemas.common import ErrorResponse, ErrorCode

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
    dependencies=[Depends(get_current_user)],
)

# ---------------------------------------------------------------------------
# Список сотрудников (краткая информация)
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[EmployeePublic])
async def list_employees(session: AsyncSession = Depends(get_async_session)):
    try:
        q = (
            select(
                Employee.id,
                Employee.first_name,
                Employee.last_name,
                Employee.email,
                Employee.title,
                Employee.status,
            )
            .where(Employee.status == "active")
            .order_by(asc(Employee.last_name), asc(Employee.first_name))
        )
        rows = (await session.execute(q)).all()

        return [
            {
                "id": row.id,
                "first_name": row.first_name,
                "last_name": row.last_name,
                "email": row.email,
                "title": row.title,
                "status": row.status,
            }
            for row in rows
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
    # 1) сам сотрудник
    emp_row = await session.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee: Employee | None = emp_row.scalar_one_or_none()

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message="Employee not found",
                status=404,
            ).model_dump(),
        )

    # 2) менеджер (если есть)
    manager_obj = None
    if employee.manager_id:
        mgr_row = await session.execute(
            select(
                Employee.id,
                Employee.first_name,
                Employee.last_name,
                Employee.title,
            ).where(Employee.id == employee.manager_id)
        )
        mgr = mgr_row.one_or_none()
        if mgr:
            manager_obj = ManagerInfo(
                id=mgr.id,
                first_name=mgr.first_name,
                last_name=mgr.last_name,
                title=mgr.title,
            )

    # 3) орг-юнит (используем lowest_org_unit_id из модели Employee)
    org_unit_obj = None
    if employee.lowest_org_unit_id:
        ou_row = await session.execute(
            select(
                OrgUnit.id,
                OrgUnit.name,
                OrgUnit.unit_type,
            ).where(OrgUnit.id == employee.lowest_org_unit_id)
        )
        ou = ou_row.one_or_none()
        if ou:
            org_unit_obj = OrgUnitInfo(
                id=ou.id,
                name=ou.name,
                unit_type=ou.unit_type,
            )

    # 4) формируем ответ (без команд и прочего лишнего)
    try:
        return EmployeeDetail(
            id=employee.id,
            email=employee.email,
            first_name=employee.first_name,
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
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.single(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to build employee detail: {e}",
                status=500,
            ).model_dump(),
        )
