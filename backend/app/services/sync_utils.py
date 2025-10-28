from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, insert
from app.models.org_unit import OrgUnit
from app.models.team import Team
from app.models.employee import Employee
from app.models.sync import SyncJob, SyncRecord
from app.models.employee_team import EmployeeTeam


# ----------------------------------------
# Вспомогательная функция
# ----------------------------------------

async def _log_sync_record(
    session: AsyncSession,
    job_id: int,
    entity_type: str,
    external_ref: str,
    local_id: Optional[int],
    action: str,
    status: str,
    message: Optional[str] = None,
):
    """Создаёт запись SyncRecord."""
    rec = SyncRecord(
        job_id=job_id,
        entity_type=entity_type,
        external_ref=external_ref,
        local_id=local_id,
        action=action,
        status=status,
        message=message,
    )
    session.add(rec)


# ----------------------------------------
# 1. OrgUnits
# ----------------------------------------

async def upsert_org_units(session: AsyncSession, job_id: int, data: List[Dict[str, Any]]) -> Dict[str, int]:
    created, updated, errors = 0, 0, 0
    for item in data:
        try:
            stmt = select(OrgUnit).where(OrgUnit.external_ref == item["external_ref"])
            res = await session.execute(stmt)
            org_unit = res.scalar_one_or_none()

            if org_unit:
                org_unit.name = item["name"]
                org_unit.unit_type = item.get("unit_type")
                updated += 1
                action = "update"
            else:
                org_unit = OrgUnit(
                    external_ref=item["external_ref"],
                    name=item["name"],
                    unit_type=item.get("unit_type"),
                )
                session.add(org_unit)
                created += 1
                action = "create"

            await _log_sync_record(session, job_id, "org_unit", item["external_ref"], None, action, "applied")
        except Exception as e:
            errors += 1
            await _log_sync_record(session, job_id, "org_unit", item["external_ref"], None, "create", "error", str(e))

    return {"created": created, "updated": updated, "errors": errors}


# ----------------------------------------
# 2. Teams
# ----------------------------------------

async def upsert_teams(session: AsyncSession, job_id: int, data: List[Dict[str, Any]]) -> Dict[str, int]:
    created, updated, errors = 0, 0, 0
    for item in data:
        try:
            stmt = select(Team).where(Team.external_ref == item["external_ref"])
            res = await session.execute(stmt)
            team = res.scalar_one_or_none()

            if team:
                team.name = item["name"]
                team.description = item.get("description")
                updated += 1
                action = "update"
            else:
                team = Team(
                    external_ref=item["external_ref"],
                    name=item["name"],
                    description=item.get("description"),
                )
                session.add(team)
                created += 1
                action = "create"

            await _log_sync_record(session, job_id, "team", item["external_ref"], None, action, "applied")
        except Exception as e:
            errors += 1
            await _log_sync_record(session, job_id, "team", item["external_ref"], None, "create", "error", str(e))

    return {"created": created, "updated": updated, "errors": errors}


# ----------------------------------------
# 3. Employees — первый проход
# ----------------------------------------

async def upsert_employees_first_pass(session: AsyncSession, job_id: int, data: List[Dict[str, Any]]) -> Dict[str, int]:
    created, updated, errors = 0, 0, 0
    for item in data:
        try:
            stmt = select(Employee).where(Employee.external_ref == item["external_ref"])
            res = await session.execute(stmt)
            emp = res.scalar_one_or_none()

            if emp:
                emp.first_name = item["first_name"]
                emp.last_name = item["last_name"]
                emp.title = item["title"]
                emp.email = item["email"]
                emp.status = item["status"]
                updated += 1
                action = "update"
            else:
                emp = Employee(
                    external_ref=item["external_ref"],
                    first_name=item["first_name"],
                    last_name=item["last_name"],
                    title=item["title"],
                    email=item["email"],
                    status=item["status"],
                )
                session.add(emp)
                created += 1
                action = "create"

            await _log_sync_record(session, job_id, "employee", item["external_ref"], None, action, "applied")
        except Exception as e:
            errors += 1
            await _log_sync_record(session, job_id, "employee", item["external_ref"], None, "create", "error", str(e))

    return {"created": created, "updated": updated, "errors": errors}


# ----------------------------------------
# 4. Второй проход (связи)
# ----------------------------------------

async def apply_org_unit_managers(session: AsyncSession, job_id: int, data: List[Dict[str, Any]]):
    for item in data:
        if not item.get("manager_external_ref"):
            continue
        stmt_ou = select(OrgUnit).where(OrgUnit.external_ref == item["external_ref"])
        stmt_mgr = select(Employee).where(Employee.external_ref == item["manager_external_ref"])
        ou_res = await session.execute(stmt_ou)
        mgr_res = await session.execute(stmt_mgr)
        ou, mgr = ou_res.scalar_one_or_none(), mgr_res.scalar_one_or_none()
        if ou and mgr:
            ou.manager_id = mgr.id


async def apply_team_leads(session: AsyncSession, job_id: int, data: List[Dict[str, Any]]):
    for item in data:
        # достаём команду
        team_q = select(Team).where(Team.external_ref == item["external_ref"])
        team_res = await session.execute(team_q)
        team = team_res.scalar_one_or_none()
        if not team:
            continue

        # lead_external_ref -> team.lead_id
        lead_ref = item.get("lead_external_ref")
        if lead_ref:
            lead_q = select(Employee).where(Employee.external_ref == lead_ref)
            lead_res = await session.execute(lead_q)
            lead = lead_res.scalar_one_or_none()
            if lead:
                team.lead_id = lead.id

        # org_unit_external_ref -> team.org_unit_id
        ou_ref = item.get("org_unit_external_ref")
        if ou_ref:
            ou_q = select(OrgUnit).where(OrgUnit.external_ref == ou_ref)
            ou_res = await session.execute(ou_q)
            ou = ou_res.scalar_one_or_none()
            if ou:
                team.org_unit_id = ou.id


async def apply_team_org_units(
    session: AsyncSession,
    job_id: int,
    data: List[Dict[str, Any]],
) -> None:
    """
    Проставляет team.org_unit_id по полю org_unit_external_ref из payload.

    Логика:
    - берем external_ref команды
    - ищем саму команду
    - берем org_unit_external_ref
    - ищем OrgUnit
    - пишем team.org_unit_id = org_unit.id
    """
    for item in data:
        org_unit_ref = item.get("org_unit_external_ref")
        if not org_unit_ref:
            continue

        team_q = select(Team).where(Team.external_ref == item["external_ref"])
        team_res = await session.execute(team_q)
        team = team_res.scalar_one_or_none()
        if not team:
            continue

        ou_q = select(OrgUnit).where(OrgUnit.external_ref == org_unit_ref)
        ou_res = await session.execute(ou_q)
        ou = ou_res.scalar_one_or_none()
        if not ou:
            continue

        team.org_unit_id = ou.id


async def apply_employee_managers_and_org_units(session: AsyncSession, job_id: int, data: List[Dict[str, Any]]):
    for item in data:
        stmt_emp = select(Employee).where(Employee.external_ref == item["external_ref"])
        res_emp = await session.execute(stmt_emp)
        emp = res_emp.scalar_one_or_none()
        if not emp:
            continue

        if mgr_ref := item.get("manager_external_ref"):
            stmt_mgr = select(Employee).where(Employee.external_ref == mgr_ref)
            res_mgr = await session.execute(stmt_mgr)
            mgr = res_mgr.scalar_one_or_none()
            if mgr:
                emp.manager_id = mgr.id

        if ou_ref := item.get("primary_org_unit_external_ref"):
            stmt_ou = select(OrgUnit).where(OrgUnit.external_ref == ou_ref)
            res_ou = await session.execute(stmt_ou)
            ou = res_ou.scalar_one_or_none()
            if ou:
                emp.primary_org_unit_id = ou.id


async def apply_employee_team_memberships(
    session: AsyncSession,
    job_id: int,
    data: List[Dict[str, Any]],
):
    """
    Синхронизирует таблицу связей employee_team.
    Поля в payload employees:
      - team_external_refs: [ "TEAM-API", ... ]
      - primary_team_external_ref: "TEAM-API"
    """

    for emp_item in data:
        emp_ref = emp_item["external_ref"]

        team_ext_refs: List[str] = emp_item.get("team_external_refs", [])
        primary_team_ext_ref: Optional[str] = emp_item.get(
            "primary_team_external_ref"
        )

        # если вообще нет информации про команды — просто скипаем,
        # считаем что внешний источник не управляет membership этого человека
        if not team_ext_refs:
            continue

        # достаём сотрудника
        emp_q = select(Employee).where(Employee.external_ref == emp_ref)
        emp_res = await session.execute(emp_q)
        emp = emp_res.scalar_one_or_none()
        if not emp:
            await _log_sync_record(
                session,
                job_id=job_id,
                entity_type="employee",
                external_ref=emp_ref,
                local_id=None,
                action="update",
                status="error",
                message="team_memberships: employee not found",
            )
            continue

        # достаём команды, которые указаны у него
        team_q = select(Team).where(Team.external_ref.in_(team_ext_refs))
        team_res = await session.execute(team_q)
        target_teams: List[Team] = list(team_res.scalars())

        target_team_ids = {t.id for t in target_teams}

        # проверим, не сослались ли на несуществующую команду
        if len(target_team_ids) != len(team_ext_refs):
            missing = set(team_ext_refs) - {t.external_ref for t in target_teams}
            await _log_sync_record(
                session,
                job_id=job_id,
                entity_type="employee",
                external_ref=emp_ref,
                local_id=emp.id,
                action="update",
                status="error",
                message=(
                    "team_memberships: some teams not found: "
                    + ", ".join(sorted(missing))
                ),
            )
            # продолжаем всё равно, просто не сможем привязать отсутствующие команды

        # достаём текущие связи сотрудника
        existing_q = select(EmployeeTeam).where(EmployeeTeam.employee_id == emp.id)
        existing_res = await session.execute(existing_q)
        existing_links: List[EmployeeTeam] = list(existing_res.scalars())

        existing_team_ids = {link.team_id for link in existing_links}

        # кто лишний — удалить
        to_remove = existing_team_ids - target_team_ids
        # кого не хватает — создать
        to_add = target_team_ids - existing_team_ids

        # вычислим primary_team_id если есть primary_team_external_ref
        primary_team_id: Optional[int] = None
        if primary_team_ext_ref:
            for t in target_teams:
                if t.external_ref == primary_team_ext_ref:
                    primary_team_id = t.id
                    break

        changed = False

        # удаляем лишние связи
        if to_remove:
            del_stmt = (
                delete(EmployeeTeam)
                .where(
                    EmployeeTeam.employee_id == emp.id,
                    EmployeeTeam.team_id.in_(to_remove),
                )
            )
            await session.execute(del_stmt)
            changed = True

        # добавляем недостающие связи
        for team_id in to_add:
            is_primary = (primary_team_id == team_id)
            ins_stmt = insert(EmployeeTeam).values(
                employee_id=emp.id,
                team_id=team_id,
                position_in_team=None,
                is_primary=is_primary,
            )
            await session.execute(ins_stmt)
            changed = True

        # обновляем primary флаг для тех связей, которые уже были
        if primary_team_id is not None:
            for link in existing_links:
                should_primary = (link.team_id == primary_team_id)
                if link.is_primary != should_primary:
                    upd_stmt = (
                        update(EmployeeTeam)
                        .where(
                            EmployeeTeam.employee_id == emp.id,
                            EmployeeTeam.team_id == link.team_id,
                        )
                        .values(is_primary=should_primary)
                    )
                    await session.execute(upd_stmt)
                    changed = True

        # если что-то поменялось — логируем applied
        if changed:
            await _log_sync_record(
                session,
                job_id=job_id,
                entity_type="employee",
                external_ref=emp_ref,
                local_id=emp.id,
                action="update",
                status="applied",
                message="team memberships synced",
            )


# ----------------------------------------
# 5. ORPHANED
# ----------------------------------------

async def detect_orphaned_entities(
    session: AsyncSession,
    job: SyncJob,
    org_units_payload: List[Dict[str, Any]],
    teams_payload: List[Dict[str, Any]],
    employees_payload: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Проверяем, кто остался в БД, но не пришёл в текущем payload.
    Не удаляем, не архивим — просто пишем SyncRecord со статусом 'orphaned'.
    """

    incoming_ou_refs: Set[str] = {ou["external_ref"] for ou in org_units_payload}
    incoming_team_refs: Set[str] = {t["external_ref"] for t in teams_payload}
    incoming_emp_refs: Set[str] = {e["external_ref"] for e in employees_payload}

    orphaned_org_units = 0
    orphaned_teams = 0
    orphaned_emps = 0

    for ou in (await session.execute(select(OrgUnit))).scalars():
        if ou.external_ref not in incoming_ou_refs:
            orphaned_org_units += 1
            await _log_sync_record(session, job.id, "org_unit", ou.external_ref, ou.id, "archive", "orphaned")

    for team in (await session.execute(select(Team))).scalars():
        if team.external_ref not in incoming_team_refs:
            orphaned_teams += 1
            await _log_sync_record(session, job.id, "team", team.external_ref, team.id, "archive", "orphaned")

    for emp in (await session.execute(select(Employee))).scalars():
        if emp.external_ref not in incoming_emp_refs:
            orphaned_emps += 1
            await _log_sync_record(session, job.id, "employee", emp.external_ref, emp.id, "archive", "orphaned")

    return {
        "count": orphaned_org_units + orphaned_teams + orphaned_emps,
        "org_units": orphaned_org_units,
        "teams": orphaned_teams,
        "employees": orphaned_emps,
    }
