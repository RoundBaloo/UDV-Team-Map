from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field


class OrgNode(BaseModel):
    """Узел орг-структуры для отдачи на фронт."""
    id: int = Field(
        serialization_alias="org_unit_id",
        description="ID org_unit"
    )
    name: str = Field(..., description="Название подразделения")
    unit_type: str = Field(..., description="Тип: group/domain/legal_entity/department/direction")
    children: List["OrgNode"] = Field(
        default_factory=list,
        description="Дочерние подразделения"
    )

    class Config:
        # pydantic v2: запрет лишних полей из сервера
        extra = "forbid"
