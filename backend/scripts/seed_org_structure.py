from __future__ import annotations

"""
Скрипт обслуживания оргструктуры.

Заполняет и обновляет таблицу org_unit по описанному JSON-дереву:
добавляет новые узлы, обновляет unit_type/ad_name и soft-архивирует
отсутствующие ветки (is_archived = true).
"""

import asyncio
import os
import sys
from typing import Any, Dict, List, Optional, Set

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import insert, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db.session import async_session_maker  # noqa: E402
from app.models.org_unit import OrgUnit  # noqa: E402


ORG_TREE: Dict[str, Any] = {
    "name": "UDV Group",
    "ad_name": "UDV Group",
    "unit_type": "group",
    "children": [
        {
            "name": "UDV Digital Transformation",
            "ad_name": "UDV Digital Transformation",
            "unit_type": "domain",
            "children": [
                {
                    "name": "ТриниДата",
                    "ad_name": "ТриниДата",
                    "unit_type": "legal_entity",
                    "children": [
                        {
                            "name": "Основное подразделение",
                            "ad_name": "Основное подразделение",
                            "unit_type": "department",
                        },
                    ],
                },
                {
                    "name": "ВНЕ ОЧЕРЕДИ",
                    "ad_name": "ВНЕ ОЧЕРЕДИ",
                    "unit_type": "legal_entity",
                    "children": [
                        {
                            "name": "Основное подразделение",
                            "ad_name": "Основное подразделение",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел продуктовой разработки",
                            "ad_name": "Отдел продуктовой разработки",
                            "unit_type": "department",
                        },
                    ],
                },
                {
                    "name": "ФТ-СОФТ",
                    "ad_name": "ФТ-СОФТ",
                    "unit_type": "legal_entity",
                    "children": [
                        {
                            "name": "Администрация",
                            "ad_name": "Администрация",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел продуктовой разработки 1",
                            "ad_name": "Отдел продуктовой разработки 1",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел продуктовой разработки 2",
                            "ad_name": "Отдел продуктовой разработки 2",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел заказной разработки",
                            "ad_name": "Отдел заказной разработки",
                            "unit_type": "department",
                        },
                        {
                            "name": "Основное подразделение",
                            "ad_name": "Основное подразделение",
                            "unit_type": "department",
                            "children": [
                                {
                                    "name": "Направление аналитики и документации",
                                    "ad_name": (
                                        "Направление аналитики и документации"
                                    ),
                                    "unit_type": "direction",
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "name": "UDV Security",
            "ad_name": "UDV Security",
            "unit_type": "domain",
            "children": [
                {
                    "name": "КИТ",
                    "ad_name": "КИТ",
                    "unit_type": "legal_entity",
                    "children": [
                        {
                            "name": "Администрация",
                            "ad_name": "Администрация",
                            "unit_type": "department",
                        },
                        {
                            "name": "Департамент консалтинга",
                            "ad_name": "Департамент консалтинга",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел сопровождения информационных систем",
                            "ad_name": (
                                "Отдел сопровождения информационных систем"
                            ),
                            "unit_type": "department",
                        },
                        {
                            "name": (
                                "Департамент по работе с иностранными заказчиками"
                            ),
                            "ad_name": (
                                "Департамент по работе с иностранными заказчиками"
                            ),
                            "unit_type": "department",
                        },
                    ],
                },
                {
                    "name": "КИТ.Р",
                    "ad_name": "КИТ.Р",
                    "unit_type": "legal_entity",
                    "children": [
                        {
                            "name": "Администрация",
                            "ad_name": "Администрация",
                            "unit_type": "department",
                        },
                        {
                            "name": "Департамент разработки",
                            "ad_name": "Департамент разработки",
                            "unit_type": "department",
                        },
                        {
                            "name": "Департамент кибербезопасности",
                            "ad_name": "Департамент кибербезопасности",
                            "unit_type": "department",
                        },
                        {
                            "name": "Департамент маркетинга",
                            "ad_name": "Департамент маркетинга",
                            "unit_type": "department",
                        },
                    ],
                },
                {
                    "name": "Сайберлимфа",
                    "ad_name": "Сайберлимфа",
                    "unit_type": "legal_entity",
                    "children": [
                        {
                            "name": "Администрация",
                            "ad_name": "Администрация",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел персонала",
                            "ad_name": "Отдел персонала",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел технического сопровождения",
                            "ad_name": "Отдел технического сопровождения",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел интеграции и автоматизации",
                            "ad_name": "Отдел интеграции и автоматизации",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел продуктового менеджмента",
                            "ad_name": "Отдел продуктового менеджмента",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел разработки",
                            "ad_name": "Отдел разработки",
                            "unit_type": "department",
                            "children": [
                                {
                                    "name": "Группа серверной разработки",
                                    "ad_name": "Группа серверной разработки",
                                    "unit_type": "direction",
                                },
                                {
                                    "name": "Группа веб разработки",
                                    "ad_name": "Группа веб разработки",
                                    "unit_type": "direction",
                                },
                                {
                                    "name": "Группа аналитики",
                                    "ad_name": "Группа аналитики",
                                    "unit_type": "direction",
                                },
                                {
                                    "name": "Группа администрирования проектов",
                                    "ad_name": (
                                        "Группа администрирования проектов"
                                    ),
                                    "unit_type": "direction",
                                },
                                {
                                    "name": "Группа продуктового дизайна",
                                    "ad_name": "Группа продуктового дизайна",
                                    "unit_type": "direction",
                                },
                            ],
                        },
                        {
                            "name": "Коммерческий департамент",
                            "ad_name": "Коммерческий департамент",
                            "unit_type": "department",
                            "children": [
                                {
                                    "name": "Отдел маркетинга",
                                    "ad_name": "Отдел маркетинга",
                                    "unit_type": "direction",
                                },
                                {
                                    "name": (
                                        "Отдел технической поддержки продаж"
                                    ),
                                    "ad_name": (
                                        "Отдел технической поддержки продаж"
                                    ),
                                    "unit_type": "direction",
                                },
                            ],
                        },
                        {
                            "name": "Лаборатория кибербезопасности",
                            "ad_name": "Лаборатория кибербезопасности",
                            "unit_type": "department",
                            "children": [
                                {
                                    "name": "Производственное направление",
                                    "ad_name": "Производственное направление",
                                    "unit_type": "direction",
                                },
                                {
                                    "name": "Аналитические направление",
                                    "ad_name": "Аналитические направление",
                                    "unit_type": "direction",
                                },
                                {
                                    "name": (
                                        "Отдел документирования и локализации"
                                    ),
                                    "ad_name": (
                                        "Отдел документирования и локализации"
                                    ),
                                    "unit_type": "direction",
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "name": "UDV Services",
            "ad_name": "UDV Services",
            "unit_type": "domain",
            "children": [
                {
                    "name": "Витропс",
                    "ad_name": "Витропс",
                    "unit_type": "legal_entity",
                    "children": [
                        {
                            "name": "Администрация",
                            "ad_name": "Администрация",
                            "unit_type": "department",
                        },
                        {
                            "name": "Планово-экономический отдел",
                            "ad_name": "Планово-экономический отдел",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел поддержки 1С",
                            "ad_name": "Отдел поддержки 1С",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел кадрового делопроизводства",
                            "ad_name": "Отдел кадрового делопроизводства",
                            "unit_type": "department",
                        },
                        {
                            "name": "Юридический отдел",
                            "ad_name": "Юридический отдел",
                            "unit_type": "department",
                        },
                        {
                            "name": "Служба внутреннего сервиса",
                            "ad_name": "Служба внутреннего сервиса",
                            "unit_type": "department",
                        },
                        {
                            "name": "Отдел делопроизводства",
                            "ad_name": "Отдел делопроизводства",
                            "unit_type": "department",
                        },
                        {
                            "name": "Бухгалтерия",
                            "ad_name": "Бухгалтерия",
                            "unit_type": "department",
                        },
                    ],
                },
            ],
        },
    ],
}


async def _get_or_create_unit(
    session: AsyncSession,
    name: str,
    unit_type: str,
    parent_id: Optional[int],
    ad_name: Optional[str],
) -> OrgUnit:
    """Апсерт по (name, parent_id) с учётом архива."""

    base_filter = [
        OrgUnit.name == name,
        (
            OrgUnit.parent_id.is_(parent_id)
            if parent_id is None
            else OrgUnit.parent_id == parent_id
        ),
    ]

    active_q = select(OrgUnit).where(
        *base_filter,
        OrgUnit.is_archived.is_(False),
    )
    obj = (await session.execute(active_q)).scalar_one_or_none()
    if obj:
        changed = False
        if obj.unit_type != unit_type:
            obj.unit_type = unit_type
            changed = True
        if ad_name is not None and obj.ad_name != ad_name:
            obj.ad_name = ad_name
            changed = True
        if changed:
            session.add(obj)
        return obj

    archived_q = select(OrgUnit).where(
        *base_filter,
        OrgUnit.is_archived.is_(True),
    )
    obj_arch = (await session.execute(archived_q)).scalar_one_or_none()
    if obj_arch:
        obj_arch.is_archived = False
        changed = False
        if obj_arch.unit_type != unit_type:
            obj_arch.unit_type = unit_type
            changed = True
        if ad_name is not None and obj_arch.ad_name != ad_name:
            obj_arch.ad_name = ad_name
            changed = True
        if changed:
            session.add(obj_arch)
        return obj_arch

    stmt = (
        insert(OrgUnit)
        .values(
            name=name,
            unit_type=unit_type,
            parent_id=parent_id,
            is_archived=False,
            ad_name=ad_name,
        )
        .returning(OrgUnit)
    )
    obj = (await session.execute(stmt)).scalar_one()
    return obj


async def _upsert_subtree(
    session: AsyncSession,
    node: Dict[str, Any],
    parent_id: Optional[int],
) -> int:
    """Рекурсивно апсертит поддерево и soft-архивирует лишних детей."""

    name: str = node["name"]
    unit_type: str = node["unit_type"]
    ad_name: Optional[str] = node.get("ad_name")
    children: List[Dict[str, Any]] = node.get("children", [])

    current = await _get_or_create_unit(
        session,
        name,
        unit_type,
        parent_id,
        ad_name,
    )
    await session.flush()

    active_child_ids: Set[int] = set()
    for child in children:
        cid = await _upsert_subtree(session, child, current.id)
        active_child_ids.add(cid)

    q_children = select(OrgUnit).where(
        OrgUnit.parent_id == current.id,
        OrgUnit.is_archived.is_(False),
    )
    existing_active_children = (await session.execute(q_children)).scalars().all()
    for ch in existing_active_children:
        if ch.id not in active_child_ids:
            ch.is_archived = True
            session.add(ch)

    return current.id


async def main() -> None:
    async with async_session_maker() as session:
        await _upsert_subtree(session, ORG_TREE, parent_id=None)
        await session.commit()
    print("Org tree upserted with soft-archive.")


if __name__ == "__main__":
    asyncio.run(main())
