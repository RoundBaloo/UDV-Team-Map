# app/services/sync/normalizer.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Mapping, Any


@dataclass
class NormalizedEmployee:
    external_ref: Optional[str]
    email: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    title: Optional[str]
    manager_external_ref: Optional[str]
    company: Optional[str]
    department: Optional[str]
    # готовим почву под синхронизацию паролей
    password_hash: Optional[str] = None


def _clean_str(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return str(v)


def normalize_employee(raw: Any) -> NormalizedEmployee:
    """
    Принимает уже ПРИВЕДЁННЫЙ препроцессором словарь (или pydantic-модель с model_dump()),
    где ключи РОВНО такие:
      - external_ref, email, first_name, middle_name, last_name, title,
        manager_external_ref, company, department, (опц.) password_hash
    Возвращает строго наш контракт NormalizedEmployee.
    """
    # допускаем как dict, так и pydantic-модель
    if hasattr(raw, "model_dump"):
        d: Mapping[str, Any] = raw.model_dump()
    elif isinstance(raw, dict):
        d = raw
    else:
        raise TypeError("normalize_employee expects dict or pydantic model")

    # мягкая очистка строк (strip, пустые -> None)
    external_ref = _clean_str(d.get("external_ref"))
    email = _clean_str(d.get("email")) or ""  # email обязателен — оставим пустую строку, если вдруг
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
