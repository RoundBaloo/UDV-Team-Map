from __future__ import annotations

"""
Импорт сотрудников из data_source/seed_employees.json в таблицу employee.

Логика:
- для каждого org_unit (department / direction) создаём сотрудников из файла;
- первый сотрудник в org_unit считается руководителем этого юнита;
- остальные сотрудники получают manager_id = id руководителя юнита;
- для direction руководитель подчиняется руководителю родительского department,
  если он есть.
"""

import asyncio
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from sqlalchemy import select  # noqa: E402

from app.db.session import async_session_maker  # noqa: E402
from app.models.employee import Employee  # noqa: E402
from app.models.org_unit import OrgUnit  # noqa: E402

INPUT_PATH = Path("data_source") / "seed_employees.json"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1]
    return datetime.fromisoformat(value)


async def main() -> None:
    if not INPUT_PATH.exists():
        raise SystemExit(f"Input file not found: {INPUT_PATH}")

    raw = INPUT_PATH.read_text(encoding="utf-8")
    data: Dict[str, Any] = json.loads(raw)
    employees_data: List[Dict[str, Any]] = data.get("employees", [])

    if not employees_data:
        print("No employees in file, nothing to import.")
        return

    async with async_session_maker() as session:
        res = await session.execute(
            select(OrgUnit).where(OrgUnit.is_archived.is_(False)),
        )
        org_units: Dict[int, OrgUnit] = {ou.id: ou for ou in res.scalars().all()}

        created_count = 0
        employees_by_unit: Dict[int, List[Employee]] = {}

        for payload in employees_data:
            org_unit_id = payload["org_unit_id"]
            org_unit_type = payload["org_unit_type"]

            ou = org_units.get(org_unit_id)
            if ou is None:
                raise RuntimeError(
                    f"OrgUnit id={org_unit_id} not found in DB",
                )

            if org_unit_type == "department":
                department_id = ou.id
                direction_id = None
            elif org_unit_type == "direction":
                direction_id = ou.id
                department_id = ou.parent_id
                if department_id is None:
                    raise RuntimeError(
                        "Direction org_unit id="
                        f"{ou.id} has no parent department",
                    )
            else:
                raise RuntimeError(
                    f"Unexpected org_unit_type={org_unit_type!r}",
                )

            emp = Employee(
                external_ref=payload["external_ref"],
                email=payload["email"],
                first_name=payload["first_name"],
                middle_name=payload.get("middle_name"),
                last_name=payload["last_name"],
                title=payload["title"],
                status=payload.get("status", "active"),
                manager_id=None,
                department_id=department_id,
                direction_id=direction_id,
                bio=payload.get("bio"),
                skill_ratings=payload.get("skill_ratings"),
                work_city=payload.get("work_city"),
                work_format=payload.get("work_format"),
                time_zone=payload.get("time_zone"),
                work_phone=payload.get("work_phone"),
                mattermost_handle=payload.get("mattermost_handle"),
                telegram_handle=payload.get("telegram_handle"),
                birth_date=_parse_date(payload.get("birth_date")),
                hire_date=_parse_date(payload.get("hire_date")),
                photo_id=None,
                password_hash=payload.get("password_hash"),
                is_blocked=bool(payload.get("is_blocked", False)),
                last_login_at=_parse_datetime(payload.get("last_login_at")),
                is_admin=bool(payload.get("is_admin", False)),
            )

            session.add(emp)
            employees_by_unit.setdefault(org_unit_id, []).append(emp)
            created_count += 1

        await session.flush()

        head_by_unit: Dict[int, Employee] = {}
        for org_unit_id, emps in employees_by_unit.items():
            if not emps:
                continue
            head_by_unit[org_unit_id] = emps[0]

        for org_unit_id, emps in employees_by_unit.items():
            if not emps:
                continue
            head = head_by_unit[org_unit_id]
            for emp in emps[1:]:
                emp.manager_id = head.id
                session.add(emp)

        for org_unit_id, head in head_by_unit.items():
            ou = org_units.get(org_unit_id)
            if not ou or ou.unit_type != "direction":
                continue

            parent_id = ou.parent_id
            if parent_id is None:
                continue

            dept_head = head_by_unit.get(parent_id)
            if dept_head is None:
                continue

            head.manager_id = dept_head.id
            session.add(head)

        await session.commit()

    print(
        "Imported "
        f"{created_count} employees from {INPUT_PATH} "
        "with managers assigned.",
    )


if __name__ == "__main__":
    asyncio.run(main())
