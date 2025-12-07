from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from ldap3 import ALL, Connection, Server

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


def _to_bool_or_none(v: Any) -> bool | None:
    """Пытается привести значение к bool или None."""
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

    is_blocked_from_ad = _to_bool_or_none(item.get("is_blocked_from_ad"))
    is_in_blocked_ou = _to_bool_or_none(item.get("is_in_blocked_ou"))

    password_hash = _clean_str(item.get("password_hash"))

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


def _safe_str(value: Any | None) -> str | None:
    """Преобразует значение в строку, обрезает пробелы, пустое → None."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        if not value:
            return None
        value = value[0]
    s = str(value).strip()
    return s or None


def _guid_to_str(raw: Any) -> str | None:
    """Преобразует objectGUID AD в строку UUID."""
    if raw is None:
        return None
    if isinstance(raw, list):
        if not raw:
            return None
        raw = raw[0]
    if isinstance(raw, uuid.UUID):
        return str(raw)
    if isinstance(raw, (bytes, bytearray)):
        try:
            return str(uuid.UUID(bytes_le=bytes(raw)))
        except ValueError:
            return None
    if isinstance(raw, str):
        return raw or None
    return None


def _extract_middle_name(
    last_name: str | None,
    first_name: str | None,
    display_name: str | None,
) -> str | None:
    """Пытается вытащить отчество из displayName.

    Ожидаемый формат: 'Фамилия Имя Отчество'.
    Если формат другой — возвращает None.
    """
    if not display_name:
        return None

    parts = display_name.strip().split()
    if len(parts) < 3:
        return None

    ln = (last_name or "").strip().lower()
    fn = (first_name or "").strip().lower()

    if parts[0].strip().lower() != ln:
        return None
    if parts[1].strip().lower() != fn:
        return None

    middle = " ".join(parts[2:]).strip()
    return middle or None


def _build_sync_payloads_from_ldap(
    entries: list[Any],
) -> list[SyncEmployeePayload]:
    """Преобразует список LDAP-записей в SyncEmployeePayload."""
    dn_to_guid: dict[str, str] = {}

    for entry in entries:
        attrs = entry.entry_attributes_as_dict
        guid = _guid_to_str(attrs.get("objectGUID") or attrs.get("objectGuid"))
        if guid:
            dn_to_guid[str(entry.entry_dn)] = guid

    result: list[SyncEmployeePayload] = []

    for entry in entries:
        attrs = entry.entry_attributes_as_dict

        dn = str(entry.entry_dn)
        external_ref = dn_to_guid.get(dn)
        if not external_ref:
            continue

        mail = _safe_str(attrs.get("mail")) or _safe_str(
            attrs.get("userPrincipalName"),
        )
        if not mail:
            continue

        first_name = _safe_str(attrs.get("givenName")) or ""
        last_name = _safe_str(attrs.get("sn")) or ""
        display_name = _safe_str(attrs.get("displayName"))

        middle_name = _extract_middle_name(
            last_name,
            first_name,
            display_name,
        )

        title = _safe_str(attrs.get("title"))
        company = _safe_str(attrs.get("company"))
        department = _safe_str(attrs.get("department"))

        if not company and not department:
            # сервисные / технические учётки, не привязанные к оргструктуре
            print(
                f"[AD SYNC][SKIP] {mail}: no company/department "
                f"(dn={dn})",
            )
            continue

        manager_dn = _safe_str(attrs.get("manager"))
        manager_external_ref: str | None = None
        if manager_dn:
            manager_external_ref = dn_to_guid.get(manager_dn)

        uac_raw = attrs.get("userAccountControl")
        if isinstance(uac_raw, (list, tuple)):
            uac_raw = uac_raw[0] if uac_raw else None

        is_blocked_from_ad: bool | None = None
        if isinstance(uac_raw, int):
            is_blocked_from_ad = bool(uac_raw & 0x2)

        payload = SyncEmployeePayload(
            external_ref=_clean_str(external_ref),
            email=_lower_str(mail) or "",
            first_name=_clean_str(first_name) or "",
            last_name=_clean_str(last_name) or "",
            middle_name=_clean_str(middle_name),
            title=_clean_str(title),
            company=_clean_str(company),
            department=_clean_str(department),
            manager_external_ref=_clean_str(manager_external_ref),
            is_blocked_from_ad=is_blocked_from_ad,
            is_in_blocked_ou=False,
            password_hash=None,
        )
        result.append(payload)

    return result


def _load_from_ad_sync() -> list[SyncEmployeePayload]:
    """Синхронно загружает пользователей из AD и маппит в SyncEmployeePayload."""
    search_filter = "(&(objectClass=user)(!(objectClass=computer)))"

    server = Server(
        settings.AD_LDAP_HOST,
        port=settings.AD_LDAP_PORT,
        use_ssl=settings.AD_USE_SSL,
        get_info=ALL,
    )

    conn = Connection(
        server,
        user=settings.AD_BIND_USER,
        password=settings.AD_BIND_PASSWORD,
        auto_bind=True,
    )

    attributes = [
        "objectGUID",
        "sAMAccountName",
        "userPrincipalName",
        "mail",
        "givenName",
        "sn",
        "displayName",
        "title",
        "company",
        "department",
        "manager",
        "userAccountControl",
    ]

    conn.search(
        search_base=settings.AD_BASE_DN,
        search_filter=search_filter,
        attributes=attributes,
    )

    entries = list(conn.entries)
    payloads = _build_sync_payloads_from_ldap(entries)

    conn.unbind()
    return payloads


async def _load_from_ad() -> list[SyncEmployeePayload]:
    """Загружает данные для синхронизации из AD."""
    payloads = await asyncio.to_thread(_load_from_ad_sync)

    print(f"[AD SYNC] Loaded {len(payloads)} employees from AD")
    for item in payloads[:10]:
        print(item.model_dump())
        print("-----")

    return payloads


async def load_sync_payload() -> list[SyncEmployeePayload]:
    """Возвращает данные для синхронизации сотрудников."""
    if settings.SYNC_USE_TEST_FILE:
        return _load_test_from_file(settings.SYNC_INGEST_FILE_PATH)

    return await _load_from_ad()


if __name__ == "__main__":

    async def _debug() -> None:
        """Отладочный запуск: показать, что отдаёт _load_from_ad()."""
        items = await _load_from_ad()
        print(f"\nTotal items: {len(items)}")

    asyncio.run(_debug())
