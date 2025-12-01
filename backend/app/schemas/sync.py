from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator


class SyncEmployeePayload(BaseModel):
    """Единый формат сотрудника для синхронизации AD → UDV Team Map."""

    external_ref: str | None = None
    email: str

    first_name: str
    last_name: str
    middle_name: str | None = None
    title: str | None = None

    company: str | None = None
    department: str | None = None
    manager_external_ref: str | None = None

    is_blocked_from_ad: bool | None = None
    is_in_blocked_ou: bool | None = None

    password_hash: str | None = None

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        """Нормализует email: trim + lower."""
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
        """Обрезает пробелы и приводит пустые строки к None."""
        if v is None:
            return None
        s = v.strip()
        return s or None


class SyncJobSummary(BaseModel):
    """Агрегированная сводка по запуску синхронизации."""

    created: int = 0
    updated: int = 0
    archived: int = 0
    errors: int = 0


class SyncJobListItem(BaseModel):
    """Элемент списка запусков синхронизации."""

    id: int = Field(serialization_alias="job_id")
    trigger: str
    status: str

    started_date: date
    finished_date: date | None = None

    summary: SyncJobSummary


class SyncRecordItem(BaseModel):
    """Строка журнала синхронизации по одному сотруднику."""

    id: int
    external_ref: str
    action: str
    status: str
    error_code: str | None = None
    message: str | None = None


class SyncJobDetail(BaseModel):
    """Детальная информация по одному запуску синхронизации."""

    id: int = Field(serialization_alias="job_id")
    trigger: str
    status: str
    started_date: date
    finished_date: date | None = None
    summary: SyncJobSummary
    records: list[SyncRecordItem]


class SyncJobRunResponse(BaseModel):
    """Ответ при ручном запуске синхронизации."""

    job_id: int
    status: str
    summary: SyncJobSummary
