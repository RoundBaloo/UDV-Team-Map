from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.org_unit import OrgUnit


# === EMPLOYEE HELPERS ===


async def get_employee_by_external_ref(
    session: AsyncSession,
    external_ref: str | None,
) -> Employee | None:
    """Возвращает сотрудника по external_ref или None, если не найден."""
    if not external_ref:
        return None

    res = await session.execute(
        select(Employee).where(Employee.external_ref == external_ref),
    )
    return res.scalar_one_or_none()


async def get_employee_by_email(
    session: AsyncSession,
    email: str | None,
) -> Employee | None:
    """Возвращает сотрудника по email или None, если не найден."""
    if not email:
        return None

    res = await session.execute(
        select(Employee).where(Employee.email == email),
    )
    return res.scalar_one_or_none()


async def upsert_employee_core(
    session: AsyncSession,
    *,
    external_ref: str | None,
    email: str,
    first_name: str,
    last_name: str,
    middle_name: str | None,
    title: str | None,
    bio: str | None,
    skill_ratings: dict[str, Any] | None,
    lowest_org_unit_id: int | None,
    password_hash: str | None = None,
) -> tuple[Employee, bool, bool]:
    """Создаёт или обновляет сотрудника.

    Возвращает кортеж (employee, created, changed), где:
    - created=True, если сотрудник был создан;
    - changed=True, если при обновлении действительно изменились поля.
    """
    created = False
    changed = False

    existing: Employee | None = None
    if external_ref:
        res = await session.execute(
            select(Employee).where(Employee.external_ref == external_ref),
        )
        existing = res.scalar_one_or_none()

    if not existing:
        res = await session.execute(
            select(Employee).where(Employee.email == email),
        )
        existing = res.scalar_one_or_none()

    if existing:

        def set_if(field: str, value: Any) -> None:
            nonlocal changed
            current = getattr(existing, field)
            if (current or None) != (value or None):
                setattr(existing, field, value)
                changed = True

        set_if("email", email)
        set_if("first_name", first_name)
        set_if("middle_name", middle_name)
        set_if("last_name", last_name)
        set_if("title", title or "")
        set_if("bio", bio)
        set_if("skill_ratings", skill_ratings)
        set_if("lowest_org_unit_id", lowest_org_unit_id)

        if password_hash and existing.password_hash != password_hash:
            existing.password_hash = password_hash
            changed = True

        emp = existing

    else:
        emp = Employee(
            external_ref=external_ref,
            email=email,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            title=title or "",
            bio=bio,
            skill_ratings=skill_ratings,
            lowest_org_unit_id=lowest_org_unit_id,
            status="active",
            password_hash=password_hash,
        )
        session.add(emp)
        created = True
        changed = True

    return emp, created, changed


# === ORG_UNIT HELPERS ===


async def get_org_unit_by_name_and_type(
    session: AsyncSession,
    *,
    name: str | None,
    unit_type: str | None,
) -> OrgUnit | None:
    """Возвращает неархивный орг-юнит по имени и типу или None, если не найден."""
    if not name or not unit_type:
        return None

    res = await session.execute(
        select(OrgUnit).where(
            OrgUnit.name == name,
            OrgUnit.unit_type == unit_type,
            OrgUnit.is_archived.is_(False),
        ),
    )
    return res.scalar_one_or_none()
