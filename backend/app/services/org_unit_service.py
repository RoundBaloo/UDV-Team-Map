from __future__ import annotations

from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org_unit import OrgUnit
from app.models.employee import Employee

from app.schemas.org_structure import OrgNode


async def build_org_tree(session: AsyncSession) -> OrgNode:
    """
    Собираем и возвращаем дерево орг-структуры, начиная с
    корня {name='UDV Group', unit_type='group'}.
    Архивные юниты (is_archived = true) игнорируем.
    """

    rows = (
        await session.execute(
            select(
                OrgUnit.id,
                OrgUnit.name,
                OrgUnit.unit_type,
                OrgUnit.parent_id,
            ).where(OrgUnit.is_archived == False)
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
        # Сортировка детей по названию, чтобы ответ был стабильным
        child_ids.sort(key=lambda cid: by_id[cid]["name"].lower())

        return OrgNode(
            id=node["id"],
            name=node["name"],
            unit_type=node["unit_type"],
            children=[attach_children(cid) for cid in child_ids],
        )

    return attach_children(root_id)


async def get_employees_of_unit(
    session,
    org_unit_id: int,
    active_only: bool = True,
) -> List[Employee]:
    """
    Вернёт сотрудников, у которых lowest_org_unit_id = org_unit_id.
    Предзагружаем manager и lowest_org_unit, чтобы не словить MissingGreenlet.
    """
    stmt = (
        select(Employee)
        .where(Employee.lowest_org_unit_id == org_unit_id)
        .options(
            selectinload(Employee.manager),
            selectinload(Employee.lowest_org_unit),
        )
    )
    if active_only:
        stmt = stmt.where(Employee.status == "active")
    result = await session.execute(stmt.order_by(Employee.last_name.asc(), Employee.first_name.asc()))
    return result.scalars().all()