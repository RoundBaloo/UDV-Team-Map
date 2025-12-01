from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.employee import Employee
from app.models.org_unit import OrgUnit


SEARCH_DEFAULT_LIMIT: int = 10
TRGM_SIM_THRESHOLD: float = 0.25


async def get_all_employees(session: AsyncSession) -> list[Employee]:
    """Возвращает всех активных сотрудников с предзагрузкой связей."""
    res = await session.execute(
        select(Employee)
        .where(Employee.status == "active")
        .options(
            selectinload(Employee.manager),
            selectinload(Employee.department),
            selectinload(Employee.direction),
        )
        .order_by(
            Employee.last_name.asc(),
            Employee.first_name.asc(),
            Employee.id.asc(),
        ),
    )
    return list(res.scalars().all())


async def get_employee_by_id(
    session: AsyncSession,
    employee_id: int,
) -> Employee | None:
    """Возвращает сотрудника по ID без загрузки связей."""
    res = await session.execute(
        select(Employee).where(Employee.id == employee_id),
    )
    return res.scalar_one_or_none()


async def get_employee_with_refs(
    session: AsyncSession,
    employee_id: int,
) -> Employee | None:
    """Возвращает сотрудника по ID с менеджером и орг-юнитами."""
    res = await session.execute(
        select(Employee)
        .where(Employee.id == employee_id)
        .options(
            selectinload(Employee.manager).load_only(
                Employee.id,
                Employee.first_name,
                Employee.last_name,
                Employee.title,
            ),
            selectinload(Employee.department).load_only(
                OrgUnit.id,
                OrgUnit.name,
                OrgUnit.unit_type,
            ),
            selectinload(Employee.direction).load_only(
                OrgUnit.id,
                OrgUnit.name,
                OrgUnit.unit_type,
            ),
        ),
    )
    return res.scalar_one_or_none()


def _set_if_changed(obj: Employee, field: str, value: Any) -> bool:
    """Устанавливает поле, если значение действительно изменилось."""
    current = getattr(obj, field)
    norm_current = current if current not in ("",) else None
    norm_value = value if value not in ("",) else None
    if norm_current != norm_value:
        setattr(obj, field, value)
        return True
    return False


async def apply_self_update(
    session: AsyncSession,
    user: Employee,
    payload: dict[str, Any],
) -> bool:
    """Применяет изменения, отправленные самим пользователем.

    Возвращает True, если данные сотрудника были изменены.
    """
    allowed = (
        "middle_name",
        "bio",
        "skill_ratings",
        "work_phone",
        "mattermost_handle",
        "telegram_handle",
        "birth_date",
        "work_city",
        "work_format",
        "time_zone",
        "hire_date",
    )

    changed = False
    for key in allowed:
        if key in payload:
            changed |= _set_if_changed(user, key, payload[key])

    if changed:
        session.add(user)

    return changed


async def apply_admin_update(
    session: AsyncSession,
    user: Employee,
    payload: dict[str, Any],
) -> bool:
    """Применяет изменения, отправленные администратором.

    Возвращает True, если данные сотрудника были изменены.
    """
    allowed = (
        "middle_name",
        "bio",
        "skill_ratings",
        "work_phone",
        "mattermost_handle",
        "telegram_handle",
        "birth_date",
        "work_city",
        "work_format",
        "time_zone",
        "hire_date",
        "is_admin",
        "is_blocked",
    )

    changed = False
    for key in allowed:
        if key in payload:
            changed |= _set_if_changed(user, key, payload[key])

    if changed:
        session.add(user)

    return changed


async def search_employees(
    session: AsyncSession,
    q: str | None = None,
    org_unit_id: int | None = None,
) -> list[Employee]:
    """Ищет сотрудников по ФИО, должности и био с учётом FTS и триграмм.

    org_unit_id трактуется как «нижний» орг-юнит:
    - если direction_id не NULL — берётся направление;
    - иначе используется department_id.
    """
    base = select(Employee).where(Employee.status == "active")

    if org_unit_id is not None:
        base = base.where(
            or_(
                Employee.direction_id == org_unit_id,
                and_(
                    Employee.direction_id.is_(None),
                    Employee.department_id == org_unit_id,
                ),
            ),
        )

    if not q or not q.strip():
        base = base.order_by(
            Employee.last_name.asc(),
            Employee.first_name.asc(),
        )
        return (await session.execute(base)).scalars().all()

    q_raw = q.strip()

    tsq = func.websearch_to_tsquery("russian", q_raw)
    ts_match = Employee.search_tsv.op("@@")(tsq)
    ts_rank = func.ts_rank_cd(Employee.search_tsv, tsq)

    normalized_q = func.unaccent(func.lower(literal(q_raw)))

    lname = func.unaccent(
        func.lower(func.coalesce(Employee.last_name, "")),
    )
    fname = func.unaccent(
        func.lower(func.coalesce(Employee.first_name, "")),
    )
    title = func.unaccent(
        func.lower(func.coalesce(Employee.title, "")),
    )
    blob = func.coalesce(Employee.search_text_norm, "")

    sim_any = func.greatest(
        func.similarity(lname, normalized_q),
        func.similarity(fname, normalized_q),
        func.similarity(title, normalized_q),
        func.similarity(blob, normalized_q),
    )

    base = base.where(
        or_(
            ts_match,
            sim_any >= TRGM_SIM_THRESHOLD,
        ),
    )

    base = (
        base.order_by(
            ts_match.desc(),
            ts_rank.desc(),
            sim_any.desc(),
            Employee.last_name.asc(),
            Employee.first_name.asc(),
        )
        .limit(SEARCH_DEFAULT_LIMIT)
    )

    return (await session.execute(base)).scalars().all()
