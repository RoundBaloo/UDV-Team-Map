from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.media import MediaInfo


class ManagerInfo(BaseModel):
    """Краткая информация о руководителе сотрудника."""

    id: int = Field(serialization_alias="manager_id")
    first_name: str
    last_name: str
    title: str | None = None


class OrgUnitInfo(BaseModel):
    """Информация о «нижнем» орг-юните сотрудника.

    Сюда попадает либо направление (direction), либо департамент (department),
    если направления нет.
    """

    id: int = Field(serialization_alias="org_unit_id")
    name: str
    unit_type: str | None = None  # department / direction


class EmployeeDetail(BaseModel):
    """Полная карточка сотрудника для клиентского API."""

    id: int = Field(serialization_alias="employee_id")
    email: str

    first_name: str
    middle_name: str | None = None
    last_name: str
    title: str | None = None
    status: str

    work_city: str | None = None
    work_format: str | None = None
    time_zone: str | None = None

    work_phone: str | None = None
    mattermost_handle: str | None = None
    telegram_handle: str | None = None

    birth_date: date | None = None
    hire_date: date | None = None
    bio: str | None = None
    skill_ratings: dict[str, int] | None = None

    is_admin: bool = False
    is_blocked: bool = False
    last_login_at: datetime | None = None

    photo: MediaInfo | None = None
    manager: ManagerInfo | None = None
    org_unit: OrgUnitInfo | None = None


class EmployeeSelfUpdate(BaseModel):
    """Поля профиля, доступные для редактирования самим сотрудником."""

    model_config = ConfigDict(extra="forbid")

    bio: str | None = None
    skill_ratings: dict[str, int] | None = None

    work_phone: str | None = None
    mattermost_handle: str | None = None
    telegram_handle: str | None = None
    birth_date: date | None = None

    work_city: str | None = None
    work_format: str | None = Field(
        None,
        pattern="^(office|hybrid|remote)$",
    )
    time_zone: str | None = None

    hire_date: date | None = None

    @field_validator("skill_ratings")
    @classmethod
    def validate_skill_ratings_user(
        cls,
        v: dict[str, int] | None,
    ) -> dict[str, int] | None:
        """Проверяет, что уровни навыков от 1 до 5."""
        if v is None:
            return None

        for name, level in v.items():
            if level is None:
                raise ValueError(
                    f"Уровень навыка '{name}' должен быть указан (1–5).",
                )
            if not 1 <= int(level) <= 5:
                raise ValueError(
                    f"Уровень навыка '{name}' должен быть в диапазоне 1–5.",
                )

        return v


class EmployeeAdminUpdate(BaseModel):
    """Поля профиля, которые может менять администратор."""

    model_config = ConfigDict(extra="forbid")

    bio: str | None = None
    skill_ratings: dict[str, int] | None = None

    work_phone: str | None = None
    mattermost_handle: str | None = None
    telegram_handle: str | None = None
    birth_date: date | None = None
    work_city: str | None = None
    work_format: str | None = Field(
        None,
        pattern="^(office|hybrid|remote)$",
    )
    time_zone: str | None = None
    hire_date: date | None = None

    direction_id: int | None = None

    is_admin: bool | None = None
    is_blocked: bool | None = None

    @field_validator("skill_ratings")
    @classmethod
    def validate_skill_ratings_admin(
        cls,
        v: dict[str, int] | None,
    ) -> dict[str, int] | None:
        """Проверяет, что уровни навыков от 1 до 5."""
        if v is None:
            return None

        for name, level in v.items():
            if level is None:
                raise ValueError(
                    f"Уровень навыка '{name}' должен быть указан (1–5).",
                )
            if not 1 <= int(level) <= 5:
                raise ValueError(
                    f"Уровень навыка '{name}' должен быть в диапазоне 1–5.",
                )

        return v


class SkillOption(BaseModel):
    """Вариант навыка для автодополнения в фильтре."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Название навыка (ключ из skill_ratings)")


class TitleItem(BaseModel):
    """Вариант названия должности для автодополнения в фильтре."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="Название должности")
