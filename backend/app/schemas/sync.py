from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class RawEmployeeAD(BaseModel):
    """Сырой сотрудник из AD (без строгой валидации email-домена)."""
    external_ref: str | None = None
    email: str
    first_name: str
    middle_name: str | None = None
    last_name: str
    title: str | None = None

    manager_external_ref: str | None = None
    company: str | None = None
    department: str | None = None

    password_hash: str | None = None

    raw: dict[str, object] = Field(default_factory=dict)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        """Нормализация email без строгой проверки домена."""
        return v.strip().lower()

    @field_validator(
        "first_name",
        "last_name",
        "middle_name",
        "title",
        "company",
        "department",
        "external_ref",
        "manager_external_ref",
        "password_hash",
    )
    @classmethod
    def _strip_text(cls, v: str | None) -> str | None:
        """Обрезаем пробелы и приводим пустые строки к None."""
        if v is None:
            return v
        s = v.strip()
        return s if s else None


__all__ = ["RawEmployeeAD"]


class OrgUnitRef(BaseModel):
    """Ссылка на узел оргструктуры по названию и типу.

    Порядок элементов в списке: от верхнего уровня к нижнему,
    например: компания -> департамент -> команда.
    """

    name: str
    unit_type: str


class NormalizedEmployee(BaseModel):
    """Нормализованный сотрудник, готовый к применению в БД.

    Apply-сервис может:
    - выбрать самый глубокий существующий org_unit из org_path,
    - найти manager_id по manager_external_ref,
    - сделать upsert сотрудника.
    """

    external_ref: str | None = None
    email: EmailStr

    first_name: str
    last_name: str
    middle_name: str | None = None

    title: str | None = None

    org_path: list[OrgUnitRef] = Field(default_factory=list)

    manager_external_ref: str | None = None
    manager_full_name: str | None = None

    received_at: datetime = Field(default_factory=datetime.utcnow)


class SyncEmployeesIngestRequest(BaseModel):
    """Пакет на вход API: пачка сырых сотрудников из AD."""

    items: list[RawEmployeeAD]


class SyncEmployeesIngestResponse(BaseModel):
    """Ответ API после приёма: ID sync_job и количество записей."""

    job_id: int
    received: int


RawEmployeeAD.model_rebuild()
