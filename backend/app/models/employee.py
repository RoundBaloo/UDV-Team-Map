from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy.dialects import postgresql

from sqlalchemy.orm import relationship

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    Computed,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Employee(Base):
    """Сотрудник компании."""

    __tablename__ = "employee"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    external_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="active",
    )

    # менеджер (руководитель сотрудника)
    manager_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="SET NULL"),
        nullable=True,
    )

    # орг-юнит, к которому относится сотрудник
    primary_org_unit_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("org_unit.id", ondelete="SET NULL"),
        nullable=True,
    )

    grade: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skills: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    work_city: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    work_format: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_zone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    work_phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    personal_phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    messengers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    birth_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    birth_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    experience_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    photo_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("media.id", ondelete="SET NULL"),
        nullable=True,
    )

    last_applied_snapshot_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("external_entity_snapshot.id", ondelete="SET NULL"),
        nullable=True,
    )

    password_hash: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # учётка заблокирована? (например, после увольнения или вручную)
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    # последний успешный вход
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # локальный флаг админа портала (не связан с AD)
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    # STORED tsvector
    search_tsv: Mapped[str] = mapped_column(
        postgresql.TSVECTOR,
        Computed(
            """
            to_tsvector(
                'simple',
                lower(
                    coalesce(first_name,'') || ' ' ||
                    coalesce(last_name,'')  || ' ' ||
                    coalesce(title,'')      || ' ' ||
                    coalesce(email,'')
                )
            )
            """,
            persisted=True,
        ),
        nullable=False,
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

    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        remote_side="Employee.id",
        foreign_keys="Employee.manager_id",
    )

    primary_org_unit: Mapped[Optional["OrgUnit"]] = relationship(
        "OrgUnit",
        foreign_keys="Employee.primary_org_unit_id",
    )

    team_links: Mapped[List["EmployeeTeam"]] = relationship(
        "EmployeeTeam",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active','dismissed')",
            name="ck_employee_status",
        ),
        CheckConstraint(
            "(work_format IS NULL) OR (work_format IN ('office','hybrid','remote'))",
            name="ck_employee_work_format",
        ),
        Index(
            "idx_employee_last_name_trgm",
            func.lower(last_name),
            postgresql_using="gin",
            postgresql_ops={func.lower(last_name).key: "gin_trgm_ops"},
        ),
        Index(
            "idx_employee_title_trgm",
            func.lower(title),
            postgresql_using="gin",
            postgresql_ops={func.lower(title).key: "gin_trgm_ops"},
        ),
        Index("idx_employee_manager_id", "manager_id"),
        Index("idx_employee_status", "status"),
        Index("idx_employee_search_tsv", "search_tsv", postgresql_using="gin"),
    )
