# так как мы знаем формат приходящего файла, то настраиваем препроцессинг
# под него. В будущем, будет изменено на ad, пока формат такой
"""Препроцессинг входных данных синхронизации сотрудников.

Ожидаемый формат payload из JSON-файла:

[
  {
    "external_ref": "E1001",
    "email": "ivan.petrov@example.com",
    "first_name": "Иван",
    "middle_name": "Петрович",
    "last_name": "Петров",
    "title": "Backend Developer",
    "manager_external_ref": "E1003",
    "company": "UDV Group",
    "department": "Платформа",
    "is_admin": false,
    "password_hash": "...bcrypt..."
  },
  ...
]

Т. е. просто JSON-массив словарей. Любой другой формат считается ошибкой.
"""

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
    """Преобразует один элемент JSON в RawEmployeeAD без сложной логики."""
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
        password_hash=_clean_str(item.get("password_hash")),
        raw=item,
    )


def preprocess_ad_payload(payload: Any) -> list[RawEmployeeAD]:
    """Приводит payload к списку RawEmployeeAD.

    Сейчас поддерживаем только один формат:
    - payload должен быть list[dict], как в примере JSON выше.

    Любой другой формат считаем ошибкой.
    """
    if payload is None:
        return []

    if not isinstance(payload, list):
        raise ValueError(
            "preprocess_ad_payload: ожидается JSON-массив сотрудников (list[dict])."
        )

    result: list[RawEmployeeAD] = []
    for item in payload:
        if isinstance(item, dict):
            result.append(_to_raw_employee(item))

    return result
