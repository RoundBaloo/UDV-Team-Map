from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

# =====  RAW payload из AD (только сотрудники)  =====


class RawEmployeeAD(BaseModel):
    """Сырой сотрудник из AD (без строгой валидации email-домена)."""

    # Упрощённая схема: email — просто строка (без EmailStr),
    # чтобы пропускать локальные домены типа "udv.local".
    external_ref: str | None = None
    email: str
    first_name: str
    middle_name: str | None = None
    last_name: str
    title: str | None = None

    manager_external_ref: str | None = None
    company: str | None = None
    department: str | None = None

    # Для отладки — исходник как есть
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
    )
    @classmethod
    def _strip_text(cls, v: str | None) -> str | None:
        """Обрезаем пробелы и приводим пустые строки к None."""
        if v is None:
            return v
        s = v.strip()
        return s if s else None


__all__ = ["RawEmployeeAD"]


# =====  Ссылка на орг-юнит по названию и типу  =====


class OrgUnitRef(BaseModel):
    """Ссылка на узел оргструктуры по названию и типу.

    Порядок элементов в списке: от верхнего уровня к нижнему,
    например: компания -> департамент -> команда.
    """

    name: str
    # Не жёстко валидируем здесь, чтобы не плодить несоответствий с БД.
    unit_type: str


# =====  Нормализованный сотрудник, готовый к применению  =====


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

    # Путь оргструктуры (от верхнего к нижнему).
    org_path: list[OrgUnitRef] = Field(default_factory=list)

    # Менеджер — используем внешний id; ФИО оставляем "на вырост".
    manager_external_ref: str | None = None
    manager_full_name: str | None = None

    # Системные поля
    received_at: datetime = Field(default_factory=datetime.utcnow)


# =====  Обёртки запросов  =====


class SyncEmployeesIngestRequest(BaseModel):
    """Пакет на вход API: пачка сырых сотрудников из AD."""

    items: list[RawEmployeeAD]


class SyncEmployeesIngestResponse(BaseModel):
    """Ответ API после приёма: ID sync_job и количество записей."""

    job_id: int
    received: int


RawEmployeeAD.model_rebuild()
