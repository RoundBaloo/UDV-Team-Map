from __future__ import annotations

"""Генерация файла с тестовыми сотрудниками для dev/test-среды.

Берём все неархивные org_unit с типами department/direction и
создаём для каждого по два сотрудника с заполненными полями.
"""

import asyncio
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

# Подключаем корень проекта для импорта app.*
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from app.db.session import async_session_maker  # noqa: E402
from app.models.org_unit import OrgUnit  # noqa: E402

OUTPUT_PATH: Path = Path("data_source") / "seed_employees.json"


def _make_phone(idx: int) -> str:
    return f"+7 900 000-{idx:04d}"


def _make_handles(idx: int) -> tuple[str, str]:
    handle = f"user{idx:03d}"
    return handle, f"@{handle}"


def _birth_date(idx: int) -> str:
    year = 1990 + (idx % 10)
    month = (idx % 12) + 1
    day = (idx % 27) + 1
    return date(year, month, day).isoformat()


def _hire_date(idx: int) -> str:
    year = 2015 + (idx % 10)
    month = ((idx + 3) % 12) + 1
    day = ((idx + 7) % 27) + 1
    return date(year, month, day).isoformat()


def _last_login(idx: int) -> str:
    dt = datetime(2024, 1, (idx % 28) + 1, 12, idx % 60, 0)
    return dt.isoformat() + "Z"


async def main() -> None:
    async with async_session_maker() as session:
        res = await session.execute(
            select(OrgUnit)
            .where(
                OrgUnit.is_archived.is_(False),
                OrgUnit.unit_type.in_(("department", "direction")),
            )
            .order_by(OrgUnit.id.asc()),
        )
        org_units = list(res.scalars().all())

    employees: list[dict[str, Any]] = []
    idx = 1

    for ou in org_units:
        for i in range(2):
            phone = _make_phone(idx)
            mm_handle, tg_handle = _make_handles(idx)

            emp: dict[str, Any] = {
                "org_unit_id": ou.id,
                "org_unit_type": ou.unit_type,
                "external_ref": f"EXT-{ou.id}-{i + 1}",
                "email": f"user{idx:03d}@example.com",
                "first_name": f"Имя{idx:03d}",
                "middle_name": f"Отчество{idx:03d}",
                "last_name": f"Фамилия{idx:03d}",
                "title": f"Сотрудник {ou.name}",
                "status": "active",
                "bio": (
                    "Тестовый сотрудник для подразделения "
                    f"«{ou.name}» (org_unit_id={ou.id})."
                ),
                "skill_ratings": {
                    "communication": 3 + (i % 3),
                    "hard_skills": 3 + ((idx + i) % 3),
                },
                "work_city": "Екатеринбург",
                "work_format": "hybrid",
                "time_zone": "Asia/Yekaterinburg",
                "work_phone": phone,
                "mattermost_handle": mm_handle,
                "telegram_handle": tg_handle,
                "birth_date": _birth_date(idx),
                "hire_date": _hire_date(idx),
                "password_hash": f"fake-hash-{idx:03d}",
                "is_blocked": False,
                "is_admin": False,
                "last_login_at": _last_login(idx),
            }

            employees.append(emp)
            idx += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump({"employees": employees}, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(employees)} employees into {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
