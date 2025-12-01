from __future__ import annotations

"""Генерация тестового файла для синхронизации (AD → UDV Team Map)."""

import asyncio
import json
import os
import sys
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.employee import Employee
from app.models.org_unit import OrgUnit

# Добавляем корень проекта, чтобы работали импорты app.*
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data_source",
    "employees_for_sync.json",
)


def _build_org_index(
    rows: list[tuple[int, str, str | None, str, int | None]],
) -> dict[int, dict[str, Any]]:
    """Строит индекс орг-юнитов по id."""
    by_id: dict[int, dict[str, Any]] = {}
    for oid, name, ad_name, unit_type, parent_id in rows:
        by_id[oid] = {
            "id": oid,
            "name": name,
            "ad_name": ad_name,
            "unit_type": unit_type,
            "parent_id": parent_id,
        }
    return by_id


def _find_department_and_company(
    org_units: dict[int, dict[str, Any]],
    employee: Employee,
) -> tuple[str | None, str | None]:
    """Восстанавливает department и company для сотрудника.

    Логика:
    - department:
      * если есть department_id — используем его;
      * иначе, если есть direction_id — берём parent этого org_unit.
    - company: поднимаемся от department вверх по parent_id,
      пока не найдём unit_type='legal_entity'.
    """
    if employee.department_id is None and employee.direction_id is None:
        return None, None

    dept_node: dict[str, Any] | None = None

    if employee.department_id is not None:
        dept_node = org_units.get(employee.department_id)
    elif employee.direction_id is not None:
        dir_node = org_units.get(employee.direction_id)
        if dir_node and dir_node.get("parent_id") is not None:
            dept_node = org_units.get(dir_node["parent_id"])

    if not dept_node:
        return None, None

    department = dept_node.get("ad_name") or dept_node.get("name")

    company: str | None = None
    current = dept_node
    while current and current.get("parent_id") is not None:
        parent = org_units.get(current["parent_id"])
        if not parent:
            break
        if parent.get("unit_type") == "legal_entity":
            company = parent.get("ad_name") or parent.get("name")
            break
        current = parent

    return department, company


async def _collect_sync_items(session: AsyncSession) -> list[dict[str, Any]]:
    """Собирает данные сотрудников в формат для SyncEmployeePayload."""
    org_rows = (
        await session.execute(
            select(
                OrgUnit.id,
                OrgUnit.name,
                OrgUnit.ad_name,
                OrgUnit.unit_type,
                OrgUnit.parent_id,
            ),
        )
    ).all()
    org_index = _build_org_index(org_rows)

    emp_rows = (
        await session.execute(select(Employee))
    ).scalars().all()

    emp_by_id: dict[int, Employee] = {e.id: e for e in emp_rows}

    items: list[dict[str, Any]] = []

    for e in emp_rows:
        if not e.external_ref:
            raise RuntimeError(
                f"Employee id={e.id} email={e.email} has no external_ref",
            )

        department, company = _find_department_and_company(org_index, e)

        manager_external_ref: str | None = None
        if e.manager_id is not None:
            mgr = emp_by_id.get(e.manager_id)
            if mgr and mgr.external_ref:
                manager_external_ref = mgr.external_ref

        item: dict[str, Any] = {
            "external_ref": e.external_ref,
            "email": e.email,
            "first_name": e.first_name,
            "last_name": e.last_name,
            "middle_name": e.middle_name,
            "title": e.title,
            "company": company,
            "department": department,
            "manager_external_ref": manager_external_ref,
            "is_blocked_from_ad": False,
            "is_in_blocked_ou": False,
            "password_hash": e.password_hash,
        }

        items.append(item)

    return items


async def main() -> None:
    """Генерирует JSON-файл employees_for_sync.json из текущей БД."""
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    async with async_session_maker() as session:
        items = await _collect_sync_items(session)

    payload = {"items": items}

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Written {len(items)} items to {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
