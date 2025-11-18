from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class NormalizedEmployee:
    """Нормализованный сотрудник для слоя синхронизации AD → БД."""

    external_ref: str | None
    email: str
    first_name: str
    middle_name: str | None
    last_name: str
    title: str | None
    manager_external_ref: str | None
    company: str | None
    department: str | None
    # Готовим почву под синхронизацию паролей
    password_hash: str | None = None


def _clean_str(value: Any) -> str | None:
    """Очищает строку: strip, пустые строки приводит к None."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return str(value)


def normalize_employee(raw: Any) -> NormalizedEmployee:
    """Нормализует данные сотрудника из сырого словаря/Pydantic-модели.

    Принимает уже приведённый препроцессором словарь (или Pydantic-модель
    с методом model_dump), в котором ключи ровно такие:

      - external_ref, email, first_name, middle_name, last_name, title,
        manager_external_ref, company, department, (опц.) password_hash

    Возвращает экземпляр NormalizedEmployee.
    """
    # Допускаем как dict, так и Pydantic-модель
    if hasattr(raw, "model_dump"):
        d: Mapping[str, Any] = raw.model_dump()
    elif isinstance(raw, dict):
        d = raw
    else:
        raise TypeError("normalize_employee expects dict or pydantic model")

    # Мягкая очистка строк (strip, пустые -> None)
    external_ref = _clean_str(d.get("external_ref"))
    email = _clean_str(d.get("email")) or ""  # email обязателен
    first_name = _clean_str(d.get("first_name")) or ""
    middle_name = _clean_str(d.get("middle_name"))
    last_name = _clean_str(d.get("last_name")) or ""
    title = _clean_str(d.get("title"))
    manager_external_ref = _clean_str(d.get("manager_external_ref"))
    company = _clean_str(d.get("company"))
    department = _clean_str(d.get("department"))
    password_hash = _clean_str(d.get("password_hash"))

    return NormalizedEmployee(
        external_ref=external_ref,
        email=email,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        title=title,
        manager_external_ref=manager_external_ref,
        company=company,
        department=department,
        password_hash=password_hash,
    )
