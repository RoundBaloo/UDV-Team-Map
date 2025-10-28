from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from app.providers.base_ad_provider import (
    BaseADProvider,
    SyncPayload,
)


class ADJsonProvider(BaseADProvider):
    """
    Тестовый провайдер данных оргструктуры.

    Вместо настоящего AD / LDAP он читает локальный JSON-файл
    и возвращает данные в стандартном формате SyncPayload.

    >>> provider = ADJsonProvider("data/ad_snapshot_v1.json")
    >>> snapshot = provider.load()
    >>> snapshot["employees"][0]["email"]
    'vasya.petrov@company.ru'
    """

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)

    def load(self) -> SyncPayload:
        """
        Прочитать JSON и вернуть гарантированно валидный SyncPayload:
        {
            "org_units":   [...],
            "teams":       [...],
            "employees":   [...]
        }

        Если в файле нет какого-то ключа, подставляем пустой список.
        """
        with self.path.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        org_units = raw.get("org_units", [])
        teams = raw.get("teams", [])
        employees = raw.get("employees", [])

        return {
            "org_units": org_units,
            "teams": teams,
            "employees": employees,
        }
