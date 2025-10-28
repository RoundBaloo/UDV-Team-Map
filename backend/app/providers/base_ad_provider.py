from __future__ import annotations

from typing import Protocol, TypedDict, List, Optional


class OrgUnitIn(TypedDict):
    """
    Входные данные по орг-юниту (блок / отдел / направление),
    полученные из внешней системы (пока JSON, потом AD).
    """

    external_ref: str
    # стабильный внешний ID, по которому мы матчим ту же запись между синхами

    name: str
    unit_type: str  # 'block' | 'department' | 'direction'

    manager_external_ref: Optional[str]
    # кто руководит этим юнитом (employee.external_ref)
    # может быть None

    parent_external_ref: Optional[str]
    # родительский орг-юнит (org_unit.external_ref)
    # может быть None (топ-уровень)


class TeamIn(TypedDict):
    """
    Входные данные по команде.
    """

    external_ref: str
    # стабильный внешний ID команды

    name: str
    description: Optional[str]

    org_unit_external_ref: str
    # к какому орг-юниту привязана команда

    lead_external_ref: Optional[str]
    # кто является лидом / тимлидом этой команды (employee.external_ref)
    # может быть None


class EmployeeIn(TypedDict):
    """
    Входные данные по сотруднику.
    """

    external_ref: str
    # стабильный внешний ID сотрудника в исходной системе

    email: str
    first_name: str
    last_name: str
    title: str

    status: str  # 'active' | 'dismissed'

    manager_external_ref: Optional[str]
    # чей он подчинённый (employee.external_ref)
    # может быть None (топ-менеджер)

    primary_org_unit_external_ref: Optional[str]
    # его основной орг-юнит (org_unit.external_ref)
    # может быть None у уволенных и т.п.

    bio: Optional[str]
    grade: Optional[str]
    skills: Optional[List[str]]

    work_city: Optional[str]
    work_format: Optional[str]  # 'office' | 'hybrid' | 'remote'
    time_zone: Optional[str]

    work_phone: Optional[str]
    personal_phone: Optional[str]


class SyncPayload(TypedDict):
    """
    Единый "снимок" внешней системы на момент синхронизации.
    Это то, что sync_service потребляет как вход.
    """

    org_units: List[OrgUnitIn]
    teams: List[TeamIn]
    employees: List[EmployeeIn]


class BaseADProvider(Protocol):
    """
    Абстрактный источник данных оргструктуры.

    Любой конкретный провайдер (JSON, реальный AD и т.д.)
    обязан реализовать load() и вернуть SyncPayload.

    Это единственная точка, которую нужно будет заменить,
    когда появится реальная интеграция.
    """

    def load(self) -> SyncPayload:
        """Вернуть полный снапшот org_units / teams / employees."""
        ...
