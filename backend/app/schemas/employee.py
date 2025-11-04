from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


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
    last_name: str
    email: str
    title: Optional[str] = None
    status: str


class EmployeeDetail(BaseModel):
    """Полная карточка сотрудника (без команд и лишнего)."""
    id: int
    email: str

    first_name: str
    last_name: str
    title: Optional[str] = None
    status: str

    work_city: Optional[str] = None
    work_format: Optional[str] = None
    time_zone: Optional[str] = None

    bio: Optional[str] = None
    hire_date: Optional[date] = None

    # оставляем дефолты, чтобы не спотыкаться, если БД/ORM вдруг не проставит
    is_admin: bool = False
    is_blocked: bool = False
    last_login_at: Optional[datetime] = None

    manager: Optional[ManagerInfo] = None
    org_unit: Optional[OrgUnitInfo] = None
