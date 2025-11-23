from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from app.schemas.media import MediaInfo


class ManagerInfo(BaseModel):
    """Краткая информация о руководителе сотрудника."""

    id: int = Field(serialization_alias="manager_id")
    first_name: str
    last_name: str
    title: str | None = None


class OrgUnitInfo(BaseModel):
    """Информация о наименьшем орг-юните сотрудника."""

    id: int = Field(serialization_alias="org_unit_id")
    name: str
    # Тип орг-юнита (например, legal_entity / department)
    unit_type: str | None = None


class EmployeeDetail(BaseModel):
    """Полная карточка сотрудника для клиентского API."""

    id: int = Field(serialization_alias="employee_id")
    email: str

    first_name: str
    middle_name: str | None = None
    last_name: str
    title: str | None = None
    status: str

    work_city: str | None = None
    work_format: str | None = None
    time_zone: str | None = None

    work_phone: str | None = None
    mattermost_handle: str | None = None
    telegram_handle: str | None = None

    birth_date: date | None = None
    hire_date: date | None = None
    bio: str | None = None
    skill_ratings: dict[str, Any] | None = None

    is_admin: bool = False
    is_blocked: bool = False
    last_login_at: datetime | None = None

    photo: MediaInfo | None = None
    manager: ManagerInfo | None = None
    org_unit: OrgUnitInfo | None = None


class EmployeeSelfUpdate(BaseModel):
    """Поля профиля, которые сотрудник может редактировать у себя сам."""

    model_config = ConfigDict(extra="forbid")

    middle_name: str | None = None
    bio: str | None = None
    skill_ratings: dict[str, Any] | None = None

    work_phone: str | None = None
    mattermost_handle: str | None = None
    telegram_handle: str | None = None
    birth_date: date | None = None

    work_city: str | None = None
    work_format: str | None = Field(
        None,
        pattern="^(office|hybrid|remote)$",
    )
    time_zone: str | None = None

    hire_date: date | None = None


class EmployeeAdminUpdate(BaseModel):
    """Поля, которые админ может менять у любого пользователя."""

    model_config = ConfigDict(extra="forbid")

    middle_name: str | None = None
    bio: str | None = None
    skill_ratings: dict[str, Any] | None = None

    work_phone: str | None = None
    mattermost_handle: str | None = None
    telegram_handle: str | None = None
    birth_date: date | None = None
    work_city: str | None = None
    work_format: str | None = Field(
        None,
        pattern="^(office|hybrid|remote)$",
    )
    time_zone: str | None = None
    hire_date: date | None = None

    is_admin: bool | None = None
    is_blocked: bool | None = None
