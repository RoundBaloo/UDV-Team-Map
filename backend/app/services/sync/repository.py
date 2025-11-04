# app/services/sync/repository.py
from __future__ import annotations

from typing import Optional, Tuple, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.org_unit import OrgUnit


# === EMPLOYEE HELPERS ===

async def get_employee_by_external_ref(
    session: AsyncSession, external_ref: Optional[str]
) -> Optional[Employee]:
    """Получить сотрудника по external_ref."""
    if not external_ref:
        return None
    res = await session.execute(
        select(Employee).where(Employee.external_ref == external_ref)
    )
    return res.scalar_one_or_none()


async def get_employee_by_email(
    session: AsyncSession, email: Optional[str]
) -> Optional[Employee]:
    """Получить сотрудника по email."""
    if not email:
        return None
    res = await session.execute(select(Employee).where(Employee.email == email))
    return res.scalar_one_or_none()


async def upsert_employee_core(
    session: AsyncSession,
    *,
    external_ref: Optional[str],
    email: str,
    first_name: str,
    last_name: str,
    middle_name: Optional[str],
    title: Optional[str],
    bio: Optional[str],
    skill_ratings: Optional[Dict[str, Any]],
    lowest_org_unit_id: Optional[int],
    password_hash: Optional[str] = None,   # 🆕 добавлено
) -> Tuple[Employee, bool, bool]:
    """
    Возвращает (employee, created, changed).

    changed=True — если при апдейте реально что-то поменялось.
    created=True — если сотрудник создан заново.
    """
    created = False
    changed = False

    # 1. ищем по external_ref, иначе по email
    existing = None
    if external_ref:
        res = await session.execute(
            select(Employee).where(Employee.external_ref == external_ref)
        )
        existing = res.scalar_one_or_none()

    if not existing:
        res = await session.execute(select(Employee).where(Employee.email == email))
        existing = res.scalar_one_or_none()

    # 2. если найден — обновляем поля
    if existing:

        def set_if(field: str, value):
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

        # 🧩 если пришёл новый хэш — обновляем, если пустой — не трогаем
        if password_hash and existing.password_hash != password_hash:
            existing.password_hash = password_hash
            changed = True

        emp = existing

    # 3. иначе создаём нового
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
            password_hash=password_hash,  # 🆕 сохраняем при создании
        )
        session.add(emp)
        created = True
        changed = True

    return emp, created, changed


# === ORG_UNIT HELPERS ===

async def get_org_unit_by_name_and_type(
    session: AsyncSession,
    *,
    name: Optional[str],
    unit_type: Optional[str],
) -> Optional[OrgUnit]:
    """Получить орг-юнит по имени и типу (если не архивный)."""
    if not name or not unit_type:
        return None
    res = await session.execute(
        select(OrgUnit).where(
            OrgUnit.name == name,
            OrgUnit.unit_type == unit_type,
            OrgUnit.is_archived.is_(False),
        )
    )
    return res.scalar_one_or_none()
