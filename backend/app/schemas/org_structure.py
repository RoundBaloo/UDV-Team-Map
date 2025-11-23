from __future__ import annotations
"""Pydantic-схемы для представления оргструктуры и результатов поиска по орг-юнитам."""

from typing import List

from pydantic import BaseModel, Field, ConfigDict


class OrgNode(BaseModel):
    """Узел оргструктуры для дерева (ответ /api/org/tree).

    Используется для отдачи иерархии:
    - id/org_unit_id – идентификатор узла
    - name – человекочитаемое название
    - unit_type – тип узла (group / domain / legal_entity / department / direction)
    - children – список дочерних узлов
    """

    model_config = ConfigDict(extra="forbid")

    id: int = Field(
        serialization_alias="org_unit_id",
        description="ID org_unit",
    )
    name: str = Field(description="Название подразделения")
    unit_type: str = Field(
        description=(
            "Тип: group / domain / legal_entity / department / direction"
        ),
    )
    children: List["OrgNode"] = Field(
        default_factory=list,
        description="Дочерние подразделения",
    )


class OrgPathItem(BaseModel):
    """Элемент пути до орг-юнита (от корня до текущего).

    Применяется в поисковой выдаче, чтобы фронт мог:
    - показать «хлебные крошки»,
    - понять, к какому домену / юр. лицу относится узел.
    """

    model_config = ConfigDict(extra="forbid")

    id: int = Field(
        serialization_alias="org_unit_id",
        description="ID org_unit",
    )
    name: str = Field(description="Название подразделения")
    unit_type: str = Field(
        description=(
            "Тип: group / domain / legal_entity / department / direction"
        ),
    )


class OrgUnitSearchItem(BaseModel):
    """Элемент результата поиска по орг-юнитам.

    - id/org_unit_id – найденный орг-юнит
    - name – его название
    - has_children – есть ли у него активные дочерние узлы
    - path – путь от корневого узла до этого (OrgPathItem[])
    """

    model_config = ConfigDict(extra="forbid")

    id: int = Field(
        serialization_alias="org_unit_id",
        description="ID org_unit",
    )
    name: str = Field(description="Название подразделения")
    has_children: bool = Field(
        description="Есть ли активные дочерние орг-юниты",
    )
    path: List[OrgPathItem] = Field(
        description="Путь от корня оргструктуры до данного узла",
    )
