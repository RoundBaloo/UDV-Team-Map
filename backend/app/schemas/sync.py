from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, EmailStr, field_validator


# =====  RAW payload из AD (только сотрудники)  =====

class RawEmployeeAD(BaseModel):
    # Упрощённая схема: email — просто строка (без EmailStr),
    # чтобы пропускать локальные домены типа "udv.local"
    external_ref: Optional[str] = None
    email: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    title: Optional[str] = None

    manager_external_ref: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None

    # для отладки — исходник как есть
    raw: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        # без строгой валидации: просто подрежем пробелы и приведём к lower
        return v.strip().lower()

    @field_validator("first_name", "last_name", "middle_name", "title", "company", "department", "external_ref", "manager_external_ref")
    @classmethod
    def _strip_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        s = v.strip()
        return s if s else None


__all__ = ["RawEmployeeAD"]


# =====  Ссылка на орг-юнит по названию и типу  =====

class OrgUnitRef(BaseModel):
    """
    Ссылка на узел орг.структуры по названию и типу.
    Порядок элементов в списке будет от верхнего уровня к нижнему (например: компания -> департамент -> команда).
    """
    name: str
    unit_type: str  # не жёстко валидируем здесь, чтобы не плодить несоответствий с БД


# =====  Нормализованный сотрудник, готовый к применению  =====

class NormalizedEmployee(BaseModel):
    """
    Это то, что apply-сервис уже сможет применить к БД:
    - выбрать deepest существующий org_unit из org_path,
    - найти manager_id (по external_ref),
    - сделать upsert сотрудника.
    """
    external_ref: Optional[str] = None
    email: EmailStr

    first_name: str
    last_name: str
    middle_name: Optional[str] = None

    title: Optional[str] = None

    # путь оргструктуры (от верхнего к нижнему). apply возьмёт самый глубокий существующий.
    org_path: List[OrgUnitRef] = Field(default_factory=list)

    # менеджер — стараемся использовать внешний id; ФИО оставляем на будущее, если решим делать сопоставление по ФИО.
    manager_external_ref: Optional[str] = None
    manager_full_name: Optional[str] = None

    # системные поля
    received_at: datetime = Field(default_factory=datetime.utcnow)


# =====  Обёртки запросов  =====

class SyncEmployeesIngestRequest(BaseModel):
    """
    Пакет на вход API: «вот пачка сырых сотрудников из AD».
    """
    items: List[RawEmployeeAD]


class SyncEmployeesIngestResponse(BaseModel):
    """
    Ответ API после приёма: id sync_job, сколько записей принято.
    """
    job_id: int
    received: int


RawEmployeeAD.model_rebuild()