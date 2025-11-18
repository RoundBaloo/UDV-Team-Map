# Пока работает с JSON-подобными структурами из AD, в
# дальнейшем этот файл будет преобразовывать в нужный для
# normalizer.py формат реальные данные из AD

from __future__ import annotations

from typing import Any

from app.schemas.sync import RawEmployeeAD


def _clean_str(value: str | None) -> str | None:
    """Обрезает пробелы, пустые строки приводит к None."""
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _lower_str(value: str | None) -> str | None:
    """Нормализует строку: trim + lower."""
    value = _clean_str(value)
    return value.lower() if value else None


def _to_raw_employee(item: dict[str, Any]) -> RawEmployeeAD:
    """Преобразует элемент словаря AD в RawEmployeeAD без сложной логики."""
    return RawEmployeeAD(
        external_ref=_clean_str(item.get("external_ref")),
        email=_lower_str(item.get("email")),
        first_name=_clean_str(item.get("first_name")) or "",
        last_name=_clean_str(item.get("last_name")) or "",
        middle_name=_clean_str(item.get("middle_name")),
        title=_clean_str(item.get("title")),
        company=_clean_str(item.get("company")),
        department=_clean_str(item.get("department")),
        manager_external_ref=_clean_str(item.get("manager_external_ref")),
        manager_full_name=_clean_str(item.get("manager_full_name")),
        raw=item,
    )


def preprocess_ad_payload(payload: Any) -> list[RawEmployeeAD]:
    """Приводит произвольный payload к списку RawEmployeeAD.

    Поддерживаемые варианты:
      - dict (одна запись)
      - list[dict] (много записей)
      - обёртки вида {"items": [...]}, {"employees": [...]}, {"data": [...]}
    """
    if payload is None:
        return []

    if isinstance(payload, dict):
        for key in ("items", "employees", "data"):
            if isinstance(payload.get(key), list):
                return [
                    _to_raw_employee(x) for x in payload[key] if isinstance(x, dict)
                ]
        return [_to_raw_employee(payload)]

    if isinstance(payload, list):
        return [_to_raw_employee(x) for x in payload if isinstance(x, dict)]

    raise ValueError("preprocess_ad_payload: ожидаются dict / list[dict]")
