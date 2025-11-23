from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import select, func, literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.employee import Employee
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
            ).where(OrgUnit.is_archived.is_(False))
        )
    ).all()

    if not rows:
        raise ValueError("Org structure is empty (no active org units)")

    by_id: Dict[int, Dict] = {}
    children_of: Dict[Optional[int], List[int]] = {}

    for rid, name, unit_type, parent_id in rows:
        by_id[rid] = {
            "id": rid,
            "name": name,
            "unit_type": unit_type,
            "parent_id": parent_id,
        }
        children_of.setdefault(parent_id, []).append(rid)

    root_id: Optional[int] = None
    for rid, node in by_id.items():
        if node["name"] == "UDV Group" and node["unit_type"] == "group":
            root_id = rid
            break

    if root_id is None:
        raise ValueError("Root node 'UDV Group' with unit_type='group' not found")

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
) -> tuple[Dict[int, Dict], Dict[Optional[int], List[int]]]:
    """Загружает все орг-юниты в словари by_id и children_of."""

    rows = (
        await session.execute(
            select(
                OrgUnit.id,
                OrgUnit.name,
                OrgUnit.unit_type,
                OrgUnit.parent_id,
                OrgUnit.is_archived,
            )
        )
    ).all()

    by_id: Dict[int, Dict] = {}
    children_of: Dict[Optional[int], List[int]] = {}

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


def _build_path(by_id: Dict[int, Dict], org_unit_id: int) -> List[OrgPathItem]:
    """Собирает путь от корня до org_unit_id по parent_id."""

    path: List[OrgPathItem] = []
    current_id: Optional[int] = org_unit_id

    while current_id is not None and current_id in by_id:
        node = by_id[current_id]
        path.append(
            OrgPathItem(
                id=node["id"],
                name=node["name"],
                unit_type=node["unit_type"],
            )
        )
        current_id = node["parent_id"]

    path.reverse()
    return path


def _matches_filters(
    path: List[OrgPathItem],
    domain_id: Optional[int],
    legal_entity_id: Optional[int],
) -> bool:
    """Проверяет, удовлетворяет ли путь фильтрам по домену / юр. лицу."""

    if domain_id is not None:
        if not any(
            item.id == domain_id and item.unit_type == "domain" for item in path
        ):
            return False

    if legal_entity_id is not None:
        if not any(
            item.id == legal_entity_id and item.unit_type == "legal_entity"
            for item in path
        ):
            return False

    return True


async def _select_candidate_ids(
    session: AsyncSession,
    q: Optional[str],
) -> List[int]:
    """Возвращает список id орг-юнитов-кандидатов для выдачи.

    - если q не задан или пустой: все неархивные узлы, отсортированные по name и id;
    - если q задан: trigram-поиск по имени с порогом ORG_UNIT_SIM_THRESHOLD,
      сортировка по similarity убыванию, затем по name, затем по id, LIMIT 7.
    """

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
    q: Optional[str] = None,
    domain_id: Optional[int] = None,
    legal_entity_id: Optional[int] = None,
) -> List[OrgUnitSearchItem]:
    """Поиск по орг-юнитам с опциональными фильтрами по домену и юр. лицу.

    Логика:
    - если q не задан: возвращаем все неархивные орг-юниты, отсортированные по имени;
    - если q задан:
        - используем similarity(unaccent(lower(name)), unaccent(lower(q))) >= threshold;
        - сортируем по similarity убыванию, затем по имени и id;
        - ограничиваем выдачу ORG_UNIT_SEARCH_LIMIT элементами.

    Для каждого результата собираем:
    - has_children: есть ли активные дочерние узлы;
    - path: путь от корня до этого орг-юнита (OrgPathItem[]).

    Фильтры:
    - domain_id: в path должен присутствовать узел с этим id и unit_type='domain';
    - legal_entity_id: в path должен присутствовать узел с этим id и unit_type='legal_entity'.
    """

    by_id, children_of = await _load_org_units_index(session)
    candidate_ids = await _select_candidate_ids(session, q)

    items: List[OrgUnitSearchItem] = []

    for oid in candidate_ids:
        node = by_id.get(oid)
        if not node:
            continue
        if node.get("is_archived"):
            continue

        path = _build_path(by_id, oid)

        if not _matches_filters(path, domain_id=domain_id, legal_entity_id=legal_entity_id):
            continue

        active_child_ids = [
            cid
            for cid in children_of.get(oid, [])
            if not by_id.get(cid, {}).get("is_archived", False)
        ]
        has_children = bool(active_child_ids)

        items.append(
            OrgUnitSearchItem(
                id=node["id"],
                name=node["name"],
                has_children=has_children,
                path=path,
            )
        )

    return items
