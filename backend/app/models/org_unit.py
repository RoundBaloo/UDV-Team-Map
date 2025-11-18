from __future__ import annotations

from datetime import datetime

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

from app.models.base import Base


class OrgUnit(Base):
    """Орг-юнит: блок / домен / юрлицо / департамент / направление."""

    __tablename__ = "org_unit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    parent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("org_unit.id", ondelete="SET NULL"),
        nullable=True,
    )

    unit_type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    manager_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="SET NULL"),
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

    # --- relationships ---

    parent: Mapped["OrgUnit"] = relationship(
        "OrgUnit",
        remote_side="OrgUnit.id",
        back_populates="children",
    )

    children: Mapped[list["OrgUnit"]] = relationship(
        "OrgUnit",
        back_populates="parent",
        passive_deletes=True,
    )

    # Сотрудники, для которых этот OrgUnit - наименьший (lowest)
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="lowest_org_unit",
        foreign_keys="Employee.lowest_org_unit_id",
        passive_deletes=True,
    )

    manager: Mapped["Employee"] = relationship(
        "Employee",
        foreign_keys="OrgUnit.manager_id",
    )

    __table_args__ = (
        CheckConstraint(
            "unit_type IN ('group','domain','legal_entity','department','direction')",
            name="ck_org_unit_unit_type",
        ),
        Index("idx_org_unit_parent_id", "parent_id"),
        Index("idx_org_unit_manager_id", "manager_id"),
        Index(
            "uq_org_unit_type_name_lower",
            func.lower(name),
            "unit_type",
            unique=True,
        ),
        Index(
            "idx_org_unit_name_trgm",
            func.lower(name),
            postgresql_using="gin",
            postgresql_ops={func.lower(name).key: "gin_trgm_ops"},
        ),
    )
