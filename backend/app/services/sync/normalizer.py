from __future__ import annotations

from dataclasses import dataclass

from app.schemas.sync import RawEmployeeAD


@dataclass
class NormalizedEmployee:
    """Нормализованный сотрудник для слоя синхронизации AD → БД.

    На этом уровне считаем, что:
      - все строки уже очищены и нормализованы на этапе препроцессинга;
      - структура данных фиксирована (RawEmployeeAD).
    Задача нормализатора – свернуть Pydantic-модель в лёгкий dataclass,
    с которым удобно работать в runner / repository.
    """

    external_ref: str | None
    email: str
    first_name: str
    middle_name: str | None
    last_name: str
    title: str | None
    manager_external_ref: str | None
    company: str | None
    department: str | None
    password_hash: str | None = None


def normalize_employee(raw: RawEmployeeAD) -> NormalizedEmployee:
    """Преобразует RawEmployeeAD в NormalizedEmployee без дополнительной очистки.

    Ожидается, что на вход всегда приходит результат работы препроцессора.
    """
    return NormalizedEmployee(
        external_ref=raw.external_ref,
        email=raw.email,
        first_name=raw.first_name,
        middle_name=raw.middle_name,
        last_name=raw.last_name,
        title=raw.title,
        manager_external_ref=raw.manager_external_ref,
        company=raw.company,
        department=raw.department,
        # password_hash может не быть в схеме, поэтому через getattr
        password_hash=getattr(raw, "password_hash", None),
    )
