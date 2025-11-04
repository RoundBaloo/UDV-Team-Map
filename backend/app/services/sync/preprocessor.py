# app/services/sync/preprocessor.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.schemas.sync import RawEmployeeAD


def _clean_str(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = str(v).strip()
    return v or None


def _lower_str(v: Optional[str]) -> Optional[str]:
    v = _clean_str(v)
    return v.lower() if v else None


def _to_raw_employee(item: Dict[str, Any]) -> RawEmployeeAD:
    """
    Ожидаем ровно наш формат ключей.
    Никаких умных преобразований — только лёгкая нормализация.
    """
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
        raw=item,  # сохраняем исходник как есть
    )


def preprocess_ad_payload(payload: Any) -> List[RawEmployeeAD]:
    """
    Принимает dict (одна запись), list[dict] (много записей),
    либо обёртку вида {"items": [...]} / {"employees": [...]}.
    Ничего лишнего — просто приводим к списку RawEmployeeAD.
    """
    if payload is None:
        return []

    # 1) если это словарь-обёртка
    if isinstance(payload, dict):
        for key in ("items", "employees", "data"):
            if isinstance(payload.get(key), list):
                return [_to_raw_employee(x) for x in payload[key] if isinstance(x, dict)]
        # 2) одиночный объект
        if isinstance(payload, dict):
            return [_to_raw_employee(payload)]

    # 3) список объектов
    if isinstance(payload, list):
        return [_to_raw_employee(x) for x in payload if isinstance(x, dict)]

    raise ValueError("preprocess_ad_payload: ожидаются dict / list[dict]")
