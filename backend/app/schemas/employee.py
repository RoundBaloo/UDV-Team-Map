from __future__ import annotations

from datetime import datetime, date
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict, PositiveInt
from app.schemas.media import MediaInfo


class ManagerInfo(BaseModel):
    id: int
    first_name: str
    last_name: str
    title: Optional[str] = None


class OrgUnitInfo(BaseModel):
    id: int
    name: str
    unit_type: Optional[str] = None  # тип орг-юнита (legal_entity / department)


class EmployeePublic(BaseModel):
    """Краткая инфа для списка сотрудников."""
    id: int
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    email: str
    title: Optional[str] = None
    status: str


class EmployeeDetail(BaseModel):
    """Полная карточка сотрудника для клиентского API."""
    id: int
    email: str

    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    title: Optional[str] = None
    status: str

    work_city: Optional[str] = None
    work_format: Optional[str] = None
    time_zone: Optional[str] = None

    work_phone: Optional[str] = None
    mattermost_handle: Optional[str] = None

    birth_date: Optional[date] = None
    hire_date: Optional[date] = None
    bio: Optional[str] = None
    skill_ratings: Optional[Dict[str, Any]] = None

    is_admin: bool = False
    is_blocked: bool = False
    last_login_at: Optional[datetime] = None

    photo: Optional[MediaInfo] = None
    manager: Optional[ManagerInfo] = None
    org_unit: Optional[OrgUnitInfo] = None


class EmployeeSelfUpdate(BaseModel):
    """
    Что сотрудник может менять у себя сам.
    """
    model_config = ConfigDict(extra="forbid")

    middle_name: Optional[str] = None
    bio: Optional[str] = None
    skill_ratings: Optional[Dict[str, Any]] = None

    work_phone: Optional[str] = None
    mattermost_handle: Optional[str] = None
    birth_date: Optional[date] = None
    photo_id: PositiveInt | None = None

    work_city: Optional[str] = None
    work_format: Optional[str] = Field(None, pattern="^(office|hybrid|remote)$")
    time_zone: Optional[str] = None

    # по нашему решению — даём редактировать сотруднику
    hire_date: Optional[date] = None


class EmployeeAdminUpdate(BaseModel):
    """
    Что админ может менять у любого пользователя.
    Включает всё, что может юзер, плюс is_admin.
    """
    model_config = ConfigDict(extra="forbid")

    middle_name: Optional[str] = None
    bio: Optional[str] = None
    skill_ratings: Optional[Dict[str, Any]] = None

    work_phone: Optional[str] = None
    mattermost_handle: Optional[str] = None
    birth_date: Optional[date] = None
    work_city: Optional[str] = None
    work_format: Optional[str] = Field(None, pattern="^(office|hybrid|remote)$")
    time_zone: Optional[str] = None
    hire_date: Optional[date] = None

    is_admin: Optional[bool] = None
    is_blocked: Optional[bool] = None
