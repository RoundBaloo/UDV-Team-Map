
from __future__ import annotations

import asyncio
import os, sys
from typing import Any, Dict, List, Optional, Tuple, Set

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_maker
from app.models.org_unit import OrgUnit

# ===== JSON-данные оргструктуры =====
ORG_TREE: Dict[str, Any] = {
    "name": "UDV Group", "unit_type": "group", "children": [
        {
            "name": "UDV Digital Transformation", "unit_type": "domain", "children": [
                {
                    "name": "ТриниДата", "unit_type": "legal_entity", "children": [
                        {"name": "Основное подразделение", "unit_type": "department"}
                    ]
                },
                {
                    "name": "ВНЕ ОЧЕРЕДИ", "unit_type": "legal_entity", "children": [
                        {"name": "Основное подразделение", "unit_type": "department"},
                        {"name": "Отдел продуктовой разработки", "unit_type": "department"}
                    ]
                },
                {
                    "name": "ФТ-СОФТ", "unit_type": "legal_entity", "children": [
                        {"name": "Администрация", "unit_type": "department"},
                        {"name": "Отдел продуктовой разработки 1", "unit_type": "department"},
                        {"name": "Отдел продуктовой разработки 2", "unit_type": "department"},
                        {"name": "Отдел заказной разработки", "unit_type": "department"},
                        {
                            "name": "Основное подразделение", "unit_type": "department", "children": [
                                {"name": "Направление аналитики и документации", "unit_type": "direction"}
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "name": "UDV Security", "unit_type": "domain", "children": [
                {
                    "name": "КИТ", "unit_type": "legal_entity", "children": [
                        {"name": "Администрация", "unit_type": "department"},
                        {"name": "Департамент консалтинга", "unit_type": "department"},
                        {"name": "Отдел сопровождения информационных систем", "unit_type": "department"},
                        {"name": "Департамент по работе с иностранными заказчиками", "unit_type": "department"}
                    ]
                },
                {
                    "name": "КИТ.Р", "unit_type": "legal_entity", "children": [
                        {"name": "Администрация", "unit_type": "department"},
                        {"name": "Департамент разработки", "unit_type": "department"},
                        {"name": "Департамент кибербезопасности", "unit_type": "department"},
                        {"name": "Департамент маркетинга", "unit_type": "department"}
                    ]
                },
                {
                    "name": "Сайберлимфа", "unit_type": "legal_entity", "children": [
                        {"name": "Администрация", "unit_type": "department"},
                        {"name": "Отдел персонала", "unit_type": "department"},
                        {"name": "Отдел технического сопровождения", "unit_type": "department"},
                        {"name": "Отдел интеграции и автоматизации", "unit_type": "department"},
                        {"name": "Отдел продуктового менеджмента", "unit_type": "department"},
                        {
                            "name": "Отдел разработки", "unit_type": "department", "children": [
                                {"name": "Группа серверной разработки", "unit_type": "direction"},
                                {"name": "Группа веб разработки", "unit_type": "direction"},
                                {"name": "Группа аналитики", "unit_type": "direction"},
                                {"name": "Группа администрирования проектов", "unit_type": "direction"},
                                {"name": "Группа продуктового дизайна", "unit_type": "direction"}
                            ]
                        },
                        {
                            "name": "Коммерческий департамент", "unit_type": "department", "children": [
                                {"name": "Отдел маркетинга", "unit_type": "direction"},
                                {"name": "Отдел технической поддержки продаж", "unit_type": "direction"}
                            ]
                        },
                        {
                            "name": "Лаборатория кибербезопасности", "unit_type": "department", "children": [
                                {"name": "Производственное направление", "unit_type": "direction"},
                                {"name": "Аналитические направление", "unit_type": "direction"},
                                {"name": "Отдел документирования и локализации", "unit_type": "direction"}
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "name": "UDV Services", "unit_type": "domain", "children": [
                {
                    "name": "Витропс", "unit_type": "legal_entity", "children": [
                        {"name": "Администрация", "unit_type": "department"},
                        {"name": "Планово-экономический отдел", "unit_type": "department"},
                        {"name": "Отдел поддержки 1С", "unit_type": "department"},
                        {"name": "Отдел кадрового делопроизводства", "unit_type": "department"},
                        {"name": "Юридический отдел", "unit_type": "department"},
                        {"name": "Служба внутреннего сервиса", "unit_type": "department"},
                        {"name": "Отдел делопроизводства", "unit_type": "department"},
                        {"name": "Бухгалтерия", "unit_type": "department"}
                    ]
                }
            ]
        }
    ]
}


async def _get_or_create_unit(
    session: AsyncSession,
    name: str,
    unit_type: str,
    parent_id: Optional[int],
) -> OrgUnit:
    """
    Апсерт по (name, parent_id).
    - Если узел найден: возвращаем его; при изменении unit_type — ОБНОВЛЯЕМ unit_type (мягкая миграция).
    - Если узел в архиве: восстанавливаем и обновляем unit_type при необходимости.
    - Если не найден: создаём.
    """
    q = select(OrgUnit).where(
        OrgUnit.name == name,
        OrgUnit.parent_id.is_(parent_id) if parent_id is None else OrgUnit.parent_id == parent_id,
        OrgUnit.is_archived == False,
    )
    obj = (await session.execute(q)).scalar_one_or_none()
    if obj:
        if obj.unit_type != unit_type:
            obj.unit_type = unit_type
            session.add(obj)
        return obj

    q_arch = select(OrgUnit).where(
        OrgUnit.name == name,
        OrgUnit.parent_id.is_(parent_id) if parent_id is None else OrgUnit.parent_id == parent_id,
        OrgUnit.is_archived == True,
    )
    obj_arch = (await session.execute(q_arch)).scalar_one_or_none()
    if obj_arch:
        obj_arch.is_archived = False
        if obj_arch.unit_type != unit_type:
            obj_arch.unit_type = unit_type
        session.add(obj_arch)
        return obj_arch

    stmt = insert(OrgUnit).values(
        name=name,
        unit_type=unit_type,
        parent_id=parent_id,
        is_archived=False,
    ).returning(OrgUnit)
    obj = (await session.execute(stmt)).scalar_one()
    return obj


async def _upsert_subtree(
    session: AsyncSession,
    node: Dict[str, Any],
    parent_id: Optional[int],
) -> int:
    """Возвращает id созданного/обновлённого узла и рекурсивно обрабатывает детей.
       Архивирует отсутствующих детей под узлом."""
    name: str = node["name"]
    unit_type: str = node["unit_type"]
    children: List[Dict[str, Any]] = node.get("children", [])

    current = await _get_or_create_unit(session, name, unit_type, parent_id)
    await session.flush()

    # Сначала апсерты детей и собираем активные id
    active_child_ids: Set[int] = set()
    for child in children:
        cid = await _upsert_subtree(session, child, current.id)
        active_child_ids.add(cid)

    # Теперь архивируем всех «лишних» детей под current, которых нет в данных
    q_children = select(OrgUnit).where(
        OrgUnit.parent_id == current.id,
        OrgUnit.is_archived == False,
    )
    existing_active_children = (await session.execute(q_children)).scalars().all()
    for ch in existing_active_children:
        if ch.id not in active_child_ids:
            ch.is_archived = True
            session.add(ch)

    return current.id


async def main():
    async with async_session_maker() as session:
        await _upsert_subtree(session, ORG_TREE, parent_id=None)
        await session.commit()
    print("✅ Org tree upserted with soft-archive.")


if __name__ == "__main__":
    asyncio.run(main())
