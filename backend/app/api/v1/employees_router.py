from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.models.employee import Employee
from app.models.team import Team
from app.models.org_unit import OrgUnit
from app.models.employee_team import EmployeeTeam
from app.schemas.employee import EmployeePublic, EmployeeDetail, ManagerInfo, OrgUnitInfo, EmployeeTeamInfo


router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("/", response_model=list[EmployeePublic])
async def list_employees(session: AsyncSession = Depends(get_async_session)):
    q = (
    select(
        Employee.id,
        Employee.first_name,
        Employee.last_name,
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
            "title": row.title,
            "status": row.status,
        }
        for row in rows
    ]


@router.get("/{employee_id}", response_model=EmployeeDetail)
async def get_employee(
    employee_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    # 1. достаем сотрудника
    emp_q = select(Employee).where(Employee.id == employee_id)
    emp_res = await session.execute(emp_q)
    employee: Employee | None = emp_res.scalar_one_or_none()

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    # 2. подтягиваем менеджера, если есть
    manager_obj = None
    if employee.manager_id:
        mgr_q = select(
            Employee.id,
            Employee.first_name,
            Employee.last_name,
            Employee.title,
        ).where(Employee.id == employee.manager_id)
        mgr_res = await session.execute(mgr_q)
        mgr_row = mgr_res.one_or_none()
        if mgr_row:
            manager_obj = ManagerInfo(
                id=mgr_row.id,
                first_name=mgr_row.first_name,
                last_name=mgr_row.last_name,
                title=mgr_row.title,
            )

    # 3. оргюнит
    org_unit_obj = None
    if employee.primary_org_unit_id:
        ou_q = select(
            OrgUnit.id,
            OrgUnit.name,
        ).where(OrgUnit.id == employee.primary_org_unit_id)
        ou_res = await session.execute(ou_q)
        ou_row = ou_res.one_or_none()
        if ou_row:
            org_unit_obj = OrgUnitInfo(
                id=ou_row.id,
                name=ou_row.name,
            )

    # 4. команды и роли
    team_q = (
        select(
            Team.id.label("team_id"),
            Team.name.label("team_name"),
            EmployeeTeam.position_in_team,
            EmployeeTeam.is_primary,
            Team.lead_id.label("lead_id"),
        )
        .join(EmployeeTeam, EmployeeTeam.team_id == Team.id)
        .where(EmployeeTeam.employee_id == employee.id)
    )

    team_rows = (await session.execute(team_q)).all()

    teams_info = [
        EmployeeTeamInfo(
            team_id=row.team_id,
            team_name=row.team_name,
            position_in_team=row.position_in_team,
            is_primary=row.is_primary,
            is_lead=(row.lead_id == employee.id),
        )
        for row in team_rows
    ]

    return EmployeeDetail(
        id=employee.id,
        first_name=employee.first_name,
        last_name=employee.last_name,
        title=employee.title,
        status=employee.status,
        work_city=employee.work_city,
        work_format=employee.work_format,
        time_zone=employee.time_zone,
        bio=employee.bio,
        experience_months=employee.experience_months,
        is_admin=employee.is_admin,
        is_blocked=employee.is_blocked,
        last_login_at=employee.last_login_at,
        manager=manager_obj,
        primary_org_unit=org_unit_obj,
        teams=teams_info,
    )
