from __future__ import annotations

from typing import Any

from sqlalchemy import (
    Integer,
    and_,
    case,
    cast,
    func,
    literal,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.employee import Employee
from app.models.org_unit import OrgUnit

SEARCH_DEFAULT_LIMIT: int = 10
TRGM_SIM_THRESHOLD: float = 0.25

SKILL_SEARCH_LIMIT: int = 20
TITLE_SEARCH_LIMIT: int = 30


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

    Возвращает:
        True, если данные сотрудника были изменены.
    """
    allowed = (
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

    Возвращает:
        True, если данные сотрудника были изменены.
    """
    allowed = (
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
        "direction_id",
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


async def _resolve_units_for_legal_entities(
    session: AsyncSession,
    legal_entity_ids: list[int],
) -> tuple[set[int], set[int]]:
    """Возвращает множества department_id и direction_id для указанных юр. лиц."""
    if not legal_entity_ids:
        return set(), set()

    res_dept = await session.execute(
        select(OrgUnit.id).where(
            OrgUnit.parent_id.in_(legal_entity_ids),
            OrgUnit.unit_type == "department",
            OrgUnit.is_archived.is_(False),
        ),
    )
    department_ids = {row[0] for row in res_dept.all()}

    if not department_ids:
        return set(), set()

    res_dir = await session.execute(
        select(OrgUnit.id).where(
            OrgUnit.parent_id.in_(department_ids),
            OrgUnit.unit_type == "direction",
            OrgUnit.is_archived.is_(False),
        ),
    )
    direction_ids = {row[0] for row in res_dir.all()}

    return department_ids, direction_ids


async def search_employees(
    session: AsyncSession,
    q: str | None = None,
    org_unit_id: int | None = None,
    *,
    skill_filters: dict[str, int] | None = None,
    titles: list[str] | None = None,
    legal_entity_ids: list[int] | None = None,
) -> list[Employee]:
    """Ищет сотрудников по ФИО, должности, био и фильтрам.

    Параметры:
        q: поисковая строка (FTS + триграммы).
        org_unit_id: фильтр по «нижнему» орг-юниту (department/direction).
        skill_filters: словарь {skill_name: level}, level 1–5,
            совпадение по точному значению для каждого указанного навыка.
        titles: список должностей; выбираются сотрудники с title в этом списке.
        legal_entity_ids: список id org_unit с unit_type='legal_entity';
            выбираются сотрудники, чьи department/direction лежат под одним
            из этих юр. лиц.

    Возвращает:
        Список ORM-объектов Employee.
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

    if titles:
        base = base.where(Employee.title.in_(titles))

    if skill_filters:
        for skill_name, level in skill_filters.items():
            json_field = Employee.skill_ratings[skill_name]
            numeric_expr = case(
                (
                    func.jsonb_typeof(json_field) == "number",
                    cast(json_field.astext, Integer),
                ),
                else_=None,
            )

        base = base.where(numeric_expr == int(level))

    if legal_entity_ids:
        dept_ids, dir_ids = await _resolve_units_for_legal_entities(
            session,
            legal_entity_ids,
        )
        if not dept_ids and not dir_ids:
            return []

        conds = []
        if dept_ids:
            conds.append(Employee.department_id.in_(dept_ids))
        if dir_ids:
            conds.append(Employee.direction_id.in_(dir_ids))

        if conds:
            base = base.where(or_(*conds))

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

    lname = func.unaccent(func.lower(func.coalesce(Employee.last_name, "")))
    fname = func.unaccent(func.lower(func.coalesce(Employee.first_name, "")))
    title = func.unaccent(func.lower(func.coalesce(Employee.title, "")))
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


async def search_skill_names(
    session: AsyncSession,
    q: str | None = None,
    limit: int = SKILL_SEARCH_LIMIT,
) -> list[str]:
    """Возвращает список имён навыков с опциональным фильтром по префиксу."""
    skills_subq = (
        select(
            func.jsonb_object_keys(Employee.skill_ratings).label("skill"),
        )
        .where(Employee.skill_ratings.is_not(None))
        .subquery()
    )

    stmt = select(func.distinct(skills_subq.c.skill))

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(skills_subq.c.skill.ilike(pattern))

    stmt = stmt.order_by(skills_subq.c.skill.asc()).limit(limit)

    res = await session.execute(stmt)
    return [row[0] for row in res.all()]


async def search_titles(
    session: AsyncSession,
    q: str | None = None,
    limit: int = TITLE_SEARCH_LIMIT,
) -> list[str]:
    """Возвращает список уникальных должностей с фильтром по префиксу (опционально)."""
    stmt = select(func.distinct(Employee.title)).where(
        Employee.title.is_not(None),
        Employee.title != "",
    )

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(Employee.title.ilike(pattern))

    stmt = stmt.order_by(Employee.title.asc()).limit(limit)

    res = await session.execute(stmt)
    return [row[0] for row in res.all()]
