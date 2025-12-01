"""Сервисы для работы с оргструктурой и поиском по орг-юнитам."""

from __future__ import annotations

from sqlalchemy import func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org_unit import OrgUnit
from app.schemas.org_structure import (
    OrgNode,
    OrgPathItem,
    OrgUnitSearchItem,
)

ORG_UNIT_SIM_THRESHOLD: float = 0.25
ORG_UNIT_SEARCH_LIMIT: int = 7


async def build_org_tree(session: AsyncSession) -> OrgNode:
    """Собирает дерево оргструктуры начиная с корня 'UDV Group' / 'group'."""
    rows = (
        await session.execute(
            select(
                OrgUnit.id,
                OrgUnit.name,
                OrgUnit.unit_type,
                OrgUnit.parent_id,
            ).where(OrgUnit.is_archived.is_(False)),
        )
    ).all()

    if not rows:
        raise ValueError("Org structure is empty (no active org units)")

    by_id: dict[int, dict] = {}
    children_of: dict[int | None, list[int]] = {}

    for rid, name, unit_type, parent_id in rows:
        by_id[rid] = {
            "id": rid,
            "name": name,
            "unit_type": unit_type,
            "parent_id": parent_id,
        }
        children_of.setdefault(parent_id, []).append(rid)

    root_id: int | None = None
    for rid, node in by_id.items():
        if node["name"] == "UDV Group" and node["unit_type"] == "group":
            root_id = rid
            break

    if root_id is None:
        raise ValueError(
            "Root node 'UDV Group' with unit_type='group' not found",
        )

    def attach_children(rid: int) -> OrgNode:
        node = by_id[rid]
        child_ids = children_of.get(rid, [])

        child_ids.sort(key=lambda cid: by_id[cid]["name"].lower())

        return OrgNode(
            id=node["id"],
            name=node["name"],
            unit_type=node["unit_type"],
            children=[attach_children(cid) for cid in child_ids],
        )

    return attach_children(root_id)


async def _load_org_units_index(
    session: AsyncSession,
) -> tuple[dict[int, dict], dict[int | None, list[int]]]:
    """Загружает все орг-юниты в индексы by_id и children_of."""
    rows = (
        await session.execute(
            select(
                OrgUnit.id,
                OrgUnit.name,
                OrgUnit.unit_type,
                OrgUnit.parent_id,
                OrgUnit.is_archived,
            ),
        )
    ).all()

    by_id: dict[int, dict] = {}
    children_of: dict[int | None, list[int]] = {}

    for rid, name, unit_type, parent_id, is_archived in rows:
        by_id[rid] = {
            "id": rid,
            "name": name,
            "unit_type": unit_type,
            "parent_id": parent_id,
            "is_archived": bool(is_archived),
        }
        children_of.setdefault(parent_id, []).append(rid)

    return by_id, children_of


def _build_path(by_id: dict[int, dict], org_unit_id: int) -> list[OrgPathItem]:
    """Собирает путь от корня до org_unit_id по parent_id."""
    path: list[OrgPathItem] = []
    current_id: int | None = org_unit_id

    while current_id is not None and current_id in by_id:
        node = by_id[current_id]
        path.append(
            OrgPathItem(
                id=node["id"],
                name=node["name"],
                unit_type=node["unit_type"],
            ),
        )
        current_id = node["parent_id"]

    path.reverse()
    return path


def _matches_filters(
    path: list[OrgPathItem],
    *,
    domain_ids: list[int] | None,
    legal_entity_ids: list[int] | None,
) -> bool:
    """Проверяет, удовлетворяет ли путь фильтрам по доменам и юрлицам.

    - domain_ids: в path должен быть узел с unit_type='domain' и id ∈ domain_ids
    - legal_entity_ids: в path должен быть узел с unit_type='legal_entity'
      и id ∈ legal_entity_ids

    Группы фильтров комбинируются по AND.
    """
    if domain_ids:
        if not any(
            item.unit_type == "domain" and item.id in domain_ids
            for item in path
        ):
            return False

    if legal_entity_ids:
        if not any(
            item.unit_type == "legal_entity" and item.id in legal_entity_ids
            for item in path
        ):
            return False

    return True


async def _select_candidate_ids(
    session: AsyncSession,
    q: str | None,
) -> list[int]:
    """Возвращает id орг-юнитов-кандидатов для поиска."""
    if not q or not q.strip():
        stmt = (
            select(OrgUnit.id)
            .where(OrgUnit.is_archived.is_(False))
            .order_by(OrgUnit.name.asc(), OrgUnit.id.asc())
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    q_raw = q.strip()

    normalized_q = func.unaccent(func.lower(literal(q_raw)))
    name_norm = func.unaccent(func.lower(OrgUnit.name))
    sim = func.similarity(name_norm, normalized_q)

    stmt = (
        select(OrgUnit.id)
        .where(
            OrgUnit.is_archived.is_(False),
            sim >= ORG_UNIT_SIM_THRESHOLD,
        )
        .order_by(sim.desc(), OrgUnit.name.asc(), OrgUnit.id.asc())
        .limit(ORG_UNIT_SEARCH_LIMIT)
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def search_org_units(
    session: AsyncSession,
    *,
    q: str | None = None,
    domain_ids: list[int] | None = None,
    legal_entity_ids: list[int] | None = None,
) -> list[OrgUnitSearchItem]:
    """Ищет орг-юниты с опциональными фильтрами по доменам и юрлицам.

    Параметры:
        q: поисковая строка по названию орг-юнита.
        domain_ids: список id org_unit с unit_type='domain'; узел должен
            находиться под одним из этих доменов.
        legal_entity_ids: список id org_unit с unit_type='legal_entity';
            узел должен находиться под одним из этих юрлиц.

    Сам домен / юр. лицо в выдачу не попадает, только их потомки.
    """
    by_id, children_of = await _load_org_units_index(session)
    candidate_ids = await _select_candidate_ids(session, q)

    items: list[OrgUnitSearchItem] = []

    for oid in candidate_ids:
        node = by_id.get(oid)
        if not node:
            continue
        if node.get("is_archived"):
            continue

        node_id = node["id"]
        node_type = node["unit_type"]

        if domain_ids and node_type == "domain" and node_id in domain_ids:
            continue
        if (
            legal_entity_ids
            and node_type == "legal_entity"
            and node_id in legal_entity_ids
        ):
            continue

        path = _build_path(by_id, oid)

        if not _matches_filters(
            path,
            domain_ids=domain_ids,
            legal_entity_ids=legal_entity_ids,
        ):
            continue

        active_child_ids = [
            cid
            for cid in children_of.get(oid, [])
            if not by_id.get(cid, {}).get("is_archived", False)
        ]
        has_children = bool(active_child_ids)

        items.append(
            OrgUnitSearchItem(
                id=node_id,
                name=node["name"],
                has_children=has_children,
                path=path,
            ),
        )

    return items


async def list_domains(session: AsyncSession) -> list[OrgUnit]:
    """Возвращает все активные домены (unit_type='domain')."""
    stmt = (
        select(OrgUnit)
        .where(
            OrgUnit.unit_type == "domain",
            OrgUnit.is_archived.is_(False),
        )
        .order_by(OrgUnit.name.asc(), OrgUnit.id.asc())
    )

    res = await session.execute(stmt)
    return list(res.scalars().all())


async def search_legal_entities(
    session: AsyncSession,
    *,
    q: str | None = None,
    domain_id: int | None = None,
    limit: int | None = None,
) -> list[OrgUnit]:
    """Поиск по юр. лицам (unit_type='legal_entity').

    Если задан domain_id, возвращаем только юр. лица под этим доменом.
    Поиск по q реализован через ILIKE '%q%'.
    """
    stmt = select(OrgUnit).where(
        OrgUnit.unit_type == "legal_entity",
        OrgUnit.is_archived.is_(False),
    )

    if domain_id is not None:
        stmt = stmt.where(OrgUnit.parent_id == domain_id)

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(OrgUnit.name.ilike(pattern))

    stmt = stmt.order_by(OrgUnit.name.asc(), OrgUnit.id.asc())

    if limit is not None:
        stmt = stmt.limit(limit)

    res = await session.execute(stmt)
    return list(res.scalars().all())
