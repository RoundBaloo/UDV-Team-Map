from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB  # если не используешь тут - можно удалить импорт

from app.models.base import Base


class OrgUnit(Base):
    """Блок / Отдел / Направление (иерархия оргструктуры)."""

    __tablename__ = "org_unit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    external_ref: Mapped[Optional[str]] = mapped_column(
        Text,
        unique=True,
        nullable=True,
    )

    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("org_unit.id", ondelete="SET NULL"),
        nullable=True,
    )

    unit_type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # руководитель юнита (employee.id)
    manager_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="SET NULL"),
        nullable=True,
    )

    last_applied_snapshot_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("external_entity_snapshot.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # -------------------
    # relationships
    # -------------------

    # parent/children оргструктуры
    parent: Mapped[Optional["OrgUnit"]] = relationship(
        "OrgUnit",
        remote_side="OrgUnit.id",
        back_populates="children",
    )

    children: Mapped[List["OrgUnit"]] = relationship(
        "OrgUnit",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # ✅ добавляем employees (чего не хватало)
    # это список сотрудников, для которых этот OrgUnit является primary_org_unit
    employees: Mapped[List["Employee"]] = relationship(
        "Employee",
        back_populates="primary_org_unit",
        foreign_keys="Employee.primary_org_unit_id",
        passive_deletes=True,
    )

    # список команд внутри юнита
    teams: Mapped[List["Team"]] = relationship(
        "Team",
        back_populates="org_unit",
        foreign_keys="Team.org_unit_id",
        passive_deletes=True,
    )

    # руководитель как объект Employee
    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys="OrgUnit.manager_id",
    )

    __table_args__ = (
        CheckConstraint(
            "unit_type IN ('block','department','direction')",
            name="ck_org_unit_unit_type",
        ),
        # индекс по parent_id
        Index("idx_org_unit_parent_id", "parent_id"),
        # индекс по manager_id
        Index("idx_org_unit_manager_id", "manager_id"),
        # триграммный индекс для поиска по названию
        Index(
            "idx_org_unit_name_trgm",
            func.lower(name),
            postgresql_using="gin",
            postgresql_ops={func.lower(name).key: "gin_trgm_ops"},
        ),
    )
