from __future__ import annotations
from typing import List, Optional, Iterable, Sequence

import re
from sqlalchemy import func, or_, select, literal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.schemas.common import ErrorResponse, ErrorCode
from app.models.media import Media
from app.models.employee import Employee
from app.models.org_unit import OrgUnit

# ---------------------------------------------------------------------------
# Search tuning constants
# ---------------------------------------------------------------------------
SEARCH_DEFAULT_LIMIT: int = 10
TRGM_SIM_THRESHOLD: float = 0.25



async def _validate_fk_media(session: AsyncSession, payload: dict):
    """Если прислали photo_id != None — проверим, что такая media существует."""
    if "photo_id" in payload and payload["photo_id"] is not None:
        pid = payload["photo_id"]
        exists = await session.execute(select(Media.id).where(Media.id == pid))
        if exists.scalar_one_or_none() is None:
            # Возвращаем аккуратную 422 вместо 500
            raise HTTPException(
                status_code=422,
                detail=ErrorResponse.single(
                    code=ErrorCode.VALIDATION_FAILED,
                    message=f"photo_id={pid} not found",
                    status=422,
                ).model_dump(),
            )


def _sanitize_payload(payload: dict) -> dict:
    clean = dict(payload)
    if "photo_id" in clean and clean["photo_id"] == 0:
        # на всякий — если вдруг обойдут Pydantic
        clean.pop("photo_id", None)
    return clean


async def get_all_employees(session: AsyncSession) -> List[Employee]:
    """
    Активные сотрудники, отсортированные по фамилии/имени.
    Предзагружаем manager и lowest_org_unit, чтобы избежать N+1 и MissingGreenlet.
    """
    res = await session.execute(
        select(Employee)
        .where(Employee.status == "active")
        .options(
            selectinload(Employee.manager),
            selectinload(Employee.lowest_org_unit),
        )
        .order_by(Employee.last_name.asc(), Employee.first_name.asc(), Employee.id.asc())
    )
    return list(res.scalars().all())


async def get_employee_by_id(session: AsyncSession, employee_id: int) -> Optional[Employee]:
    """
    Базовая загрузка без связей (если где-то нужно).
    """
    res = await session.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    return res.scalar_one_or_none()


async def get_employee_with_refs(session: AsyncSession, employee_id: int) -> Optional[Employee]:
    """
    Детальная карточка: подгружаем менеджера и орг-юнит через selectinload.
    """
    res = await session.execute(
        select(Employee)
        .where(Employee.id == employee_id)
        .options(
            selectinload(Employee.manager).load_only(
                Employee.id, Employee.first_name, Employee.last_name, Employee.title
            ),
            selectinload(Employee.lowest_org_unit).load_only(
                OrgUnit.id, OrgUnit.name, OrgUnit.unit_type
            ),
        )
    )
    return res.scalar_one_or_none()


def _set_if_changed(obj: Employee, field: str, value) -> bool:
    """Утилита: проставить, если реально изменилось (с учётом None/пустых строк)."""
    current = getattr(obj, field)
    norm_current = current if current not in ("",) else None
    norm_value = value if value not in ("",) else None
    if norm_current != norm_value:
        setattr(obj, field, value)
        return True
    return False


async def apply_self_update(session: AsyncSession, user: Employee, payload: dict) -> bool:
    """
    Применить апдейт от самого пользователя.
    Возвращает changed=True, если что-то реально поменяли.
    """
    payload = _sanitize_payload(payload)
    await _validate_fk_media(session, payload)
    allowed: Iterable[str] = (
        "middle_name", "bio", "skill_ratings",
        "work_phone", "mattermost_handle", "birth_date",
        "photo_id", "work_city", "work_format", "time_zone",
        "hire_date",
    )
    changed = False
    for key in allowed:
        if key in payload:
            changed |= _set_if_changed(user, key, payload[key])
    if changed:
        session.add(user)
    return changed


async def apply_admin_update(session: AsyncSession, user: Employee, payload: dict) -> bool:
    """
    Применить апдейт от админа.
    Возвращает changed=True, если что-то реально поменяли.
    """
    payload = _sanitize_payload(payload)
    await _validate_fk_media(session, payload)
    allowed: Iterable[str] = (
        # то, что может и обычный пользователь:
        "middle_name", "bio", "skill_ratings",
        "work_phone", "mattermost_handle", "birth_date",
        "work_city", "work_format", "time_zone", "hire_date",
        # только админ:
        "is_admin", "is_blocked",
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
    q: Optional[str] = None,
    org_unit_id: Optional[int] = None,
) -> List[Employee]:
    """
    - без q: активные сотрудники, сортировка по ФИО
    - с q: (FTS OR trigram) и ранжирование: FTS сверху, затем по similarity, затем ФИО
    """
    base = select(Employee).where(Employee.status == "active")

    if org_unit_id is not None:
        base = base.where(Employee.lowest_org_unit_id == org_unit_id)

    # без запроса — классический список
    if not q or not q.strip():
        base = base.order_by(Employee.last_name.asc(), Employee.first_name.asc())
        return (await session.execute(base)).scalars().all()

    # --- поиск ---
    q_raw = q.strip()

    # FTS по russian словарю
    tsq = func.websearch_to_tsquery('russian', q_raw)
    ts_match = Employee.search_tsv.op('@@')(tsq)
    ts_rank = func.ts_rank_cd(Employee.search_tsv, tsq)

    # НОРМАЛИЗУЕМ запрос на стороне БД (как и поле): unaccent(lower(q))
    normalized_q = func.unaccent(func.lower(literal(q_raw)))

    # НОРМАЛИЗОВАННЫЕ поля (совпадают с логикой search_text_norm)
    lname = func.unaccent(func.lower(func.coalesce(Employee.last_name, '')))
    fname = func.unaccent(func.lower(func.coalesce(Employee.first_name, '')))
    title = func.unaccent(func.lower(func.coalesce(Employee.title, '')))
    blob  = func.coalesce(Employee.search_text_norm, '')

    # similarity: берём максимум совпадения по полям
    sim_any = func.greatest(
        func.similarity(lname, normalized_q),
        func.similarity(fname, normalized_q),
        func.similarity(title, normalized_q),
        func.similarity(blob,  normalized_q),
    )

    # фильтр: FTS или мягкий trigram-порог
    base = base.where(or_(ts_match, sim_any >= TRGM_SIM_THRESHOLD))

    # сортировка: FTS сначала (match→rank), потом по similarity, затем ФИО
    base = base.order_by(
        ts_match.desc(),
        ts_rank.desc(),
        sim_any.desc(),
        Employee.last_name.asc(),
        Employee.first_name.asc(),
    ).limit(SEARCH_DEFAULT_LIMIT)

    return (await session.execute(base)).scalars().all()