from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.employee import Employee
from app.models.org_unit import OrgUnit


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
    department_id: int | None,
    password_hash: str | None = None,
    is_blocked_from_sync: bool | None = None,
    status_from_sync: str | None = None,
) -> tuple[Employee, bool, bool, bool]:
    """Создаёт или обновляет сотрудника.

    Возвращает кортеж (employee, created, changed, dismissed_now).
    """
    created = False
    changed = False
    dismissed_now = False

    existing: Employee | None = None
    if external_ref:
        res = await session.execute(
            select(Employee).where(Employee.external_ref == external_ref),
        )
        existing = res.scalar_one_or_none()

    if existing is None:
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

        if department_id is not None and existing.department_id != department_id:
            existing.department_id = department_id
            if getattr(existing, "direction_id", None) is not None:
                existing.direction_id = None
            changed = True

        if password_hash and existing.password_hash != password_hash:
            existing.password_hash = password_hash
            changed = True

        if is_blocked_from_sync:
            if not existing.is_blocked:
                existing.is_blocked = True
                changed = True

        if status_from_sync == "dismissed" and existing.status != "dismissed":
            existing.status = "dismissed"
            dismissed_now = True
            changed = True

        emp = existing
    else:
        status_value = "active"
        if status_from_sync == "dismissed":
            status_value = "dismissed"
            dismissed_now = True

        emp = Employee(
            external_ref=external_ref,
            email=email,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            title=title or "",
            department_id=department_id,
            status=status_value,
            password_hash=password_hash,
            is_blocked=bool(is_blocked_from_sync),
        )
        session.add(emp)
        created = True
        changed = True

    return emp, created, changed, dismissed_now


async def resolve_department_id_for_sync(
    session: AsyncSession,
    *,
    company: str | None,
    department: str | None,
) -> int | None:
    """Ищет департамент по (company, department) через OrgUnit.ad_name."""
    if not company or not department:
        return None

    Parent = aliased(OrgUnit)
    Child = aliased(OrgUnit)

    res = await session.execute(
        select(Child.id)
        .join(Parent, Child.parent_id == Parent.id)
        .where(
            Parent.unit_type == "legal_entity",
            Parent.ad_name == company,
            Parent.is_archived.is_(False),
            Child.unit_type == "department",
            Child.ad_name == department,
            Child.is_archived.is_(False),
        )
        .limit(1),
    )

    return res.scalar_one_or_none()
