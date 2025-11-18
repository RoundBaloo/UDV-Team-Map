from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class OrgNode(BaseModel):
    """Узел оргструктуры для отдачи на фронт."""

    id: int = Field(
        serialization_alias="org_unit_id",
        description="ID org_unit",
    )
    name: str = Field(
        ...,
        description="Название подразделения",
    )
    unit_type: str = Field(
        ...,
        description="Тип: group/domain/legal_entity/department/direction",
    )
    children: list["OrgNode"] = Field(
        default_factory=list,
        description="Дочерние подразделения",
    )

    model_config = ConfigDict(extra="forbid")
