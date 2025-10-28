from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class EmployeeTeamInfo(BaseModel):
    team_id: int
    team_name: str
    position_in_team: Optional[str]
    is_primary: bool
    is_lead: bool


class ManagerInfo(BaseModel):
    id: int
    first_name: str
    last_name: str
    title: Optional[str]


class OrgUnitInfo(BaseModel):
    id: int
    name: str


class EmployeePublic(BaseModel):
    """
    Краткая инфа (для списка сотрудников).
    Это то, что ты уже сейчас возвращаешь в /employees.
    """
    id: int
    first_name: str
    last_name: str
    title: Optional[str]
    status: str


class EmployeeDetail(BaseModel):
    """
    Полная карточка сотрудника.
    Это то, что будем возвращать в /employees/{id}.
    """
    id: int
    first_name: str
    last_name: str
    title: Optional[str]
    status: str

    work_city: Optional[str]
    work_format: Optional[str]
    time_zone: Optional[str]

    bio: Optional[str]
    experience_months: Optional[int]

    is_admin: bool
    is_blocked: bool
    last_login_at: Optional[datetime]

    manager: Optional[ManagerInfo]
    primary_org_unit: Optional[OrgUnitInfo]

    teams: List[EmployeeTeamInfo]
