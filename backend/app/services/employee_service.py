from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.employee import Employee
from app.models.media import Media
from app.models.org_unit import OrgUnit
from app.schemas.common import ErrorCode, ErrorResponse

# Параметры поиска
SEARCH_DEFAULT_LIMIT: int = 10
TRGM_SIM_THRESHOLD: float = 0.25


async def _validate_fk_media(session: AsyncSession, payload: dict[str, Any]) -> None:
    """Проверяет, что переданный photo_id существует в таблице media."""
    if "photo_id" in payload and payload["photo_id"] is not None:
        pid = payload["photo_id"]
        exists = await session.execute(
            select(Media.id).where(Media.id == pid),
        )
        if exists.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=422,
                detail=ErrorResponse.single(
                    code=ErrorCode.VALIDATION_FAILED,
                    message=f"photo_id={pid} not found",
                    status=422,
                ).model_dump(),
            )


def _sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Удаляет заведомо некорректные значения из payload (например, photo_id=0)."""
    clean = dict(payload)
    if "photo_id" in clean and clean["photo_id"] == 0:
        clean.pop("photo_id", None)
    return clean


async def get_all_employees(session: AsyncSession) -> list[Employee]:
    """Возвращает всех активных сотрудников с предзагрузкой связей."""
    res = await session.execute(
        select(Employee)
        .where(Employee.status == "active")
        .options(
            selectinload(Employee.manager),
            selectinload(Employee.lowest_org_unit),
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
    """Возвращает сотрудника по ID с менеджером и орг-юнитом."""
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
            selectinload(Employee.lowest_org_unit).load_only(
                OrgUnit.id,
                OrgUnit.name,
                OrgUnit.unit_type,
            ),
        ),
    )
    return res.scalar_one_or_none()


def _set_if_changed(obj: Employee, field: str, value: Any) -> bool:
    """Устанавливает поле, если значение реально изменилось (учитывая пустые строки)."""
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
    payload = _sanitize_payload(payload)
    await _validate_fk_media(session, payload)

    allowed = (
        "middle_name",
        "bio",
        "skill_ratings",
        "work_phone",
        "mattermost_handle",
        "birth_date",
        "photo_id",
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
    payload = _sanitize_payload(payload)
    await _validate_fk_media(session, payload)

    allowed = (
        "middle_name",
        "bio",
        "skill_ratings",
        "work_phone",
        "mattermost_handle",
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
    """Ищет сотрудников по ФИО/должности/био с учётом FTS и триграмм."""
    base = select(Employee).where(Employee.status == "active")

    if org_unit_id is not None:
        base = base.where(Employee.lowest_org_unit_id == org_unit_id)

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
