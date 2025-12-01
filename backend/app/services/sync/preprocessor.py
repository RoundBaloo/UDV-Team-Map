from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.schemas.sync import SyncEmployeePayload


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


def _to_payload(item: dict[str, Any]) -> SyncEmployeePayload:
    """Преобразует dict в SyncEmployeePayload без сложной логики."""
    external_ref = _clean_str(item.get("external_ref"))
    email = _lower_str(item.get("email")) or ""
    first_name = _clean_str(item.get("first_name")) or ""
    last_name = _clean_str(item.get("last_name")) or ""
    middle_name = _clean_str(item.get("middle_name"))
    title = _clean_str(item.get("title"))

    company = _clean_str(item.get("company"))
    department = _clean_str(item.get("department"))
    manager_external_ref = _clean_str(item.get("manager_external_ref"))

    password_hash = _clean_str(item.get("password_hash"))

    def _to_bool_or_none(v: Any) -> bool | None:
        if isinstance(v, bool):
            return v
        if v in (0, 1):
            return bool(v)
        if isinstance(v, str):
            s = v.strip().lower()
            if s in ("true", "1", "yes", "y"):
                return True
            if s in ("false", "0", "no", "n"):
                return False
        return None

    is_blocked_from_ad = _to_bool_or_none(item.get("is_blocked_from_ad"))
    is_in_blocked_ou = _to_bool_or_none(item.get("is_in_blocked_ou"))

    return SyncEmployeePayload(
        external_ref=external_ref,
        email=email,
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
        title=title,
        company=company,
        department=department,
        manager_external_ref=manager_external_ref,
        is_blocked_from_ad=is_blocked_from_ad,
        is_in_blocked_ou=is_in_blocked_ou,
        password_hash=password_hash,
    )


def _from_raw_payload(payload: Any) -> list[SyncEmployeePayload]:
    """Преобразует сырой payload в список SyncEmployeePayload.

    Поддерживаем:
    - payload = list[dict];
    - payload = {"items": [...]}.
    """
    if payload is None:
        return []

    if isinstance(payload, dict):
        if "items" in payload:
            payload = payload["items"]
        else:
            raise ValueError(
                "preprocess_ad_payload: dict-payload должен содержать ключ "
                "'items' со списком сотрудников.",
            )

    if not isinstance(payload, list):
        raise ValueError(
            "preprocess_ad_payload: ожидается JSON-массив сотрудников "
            "(list[dict]) или объект с ключом 'items'.",
        )

    result: list[SyncEmployeePayload] = []
    for item in payload:
        if isinstance(item, dict):
            result.append(_to_payload(item))

    return result


def _load_test_from_file(path_value: str) -> list[SyncEmployeePayload]:
    """Читает тестовый JSON-файл и приводит к SyncEmployeePayload."""
    path = Path(path_value)
    if not path.exists():
        raise RuntimeError(
            f"Файл для тестовой синхронизации не найден: {path}",
        )

    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Не удалось разобрать JSON из файла синхронизации: {exc}",
        ) from exc

    return _from_raw_payload(raw)


async def _load_from_ad() -> list[SyncEmployeePayload]:
    """Заглушка для реальной интеграции с AD."""
    return []


async def load_sync_payload() -> list[SyncEmployeePayload]:
    """Возвращает данные для синхронизации сотрудников."""
    if settings.SYNC_USE_TEST_FILE:
        return _load_test_from_file(settings.SYNC_INGEST_FILE_PATH)

    return await _load_from_ad()
