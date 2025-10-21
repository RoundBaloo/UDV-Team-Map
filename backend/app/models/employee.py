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
    SmallInteger,
    Text,
    func,
    Computed,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Employee(Base):
    """Сотрудник."""

    __tablename__ = "employee"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # идентификация
    external_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    # поля из внешней БД
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="active"
    )
    manager_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("employee.id", ondelete="SET NULL"), nullable=True
    )
    primary_org_unit_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("org_unit.id", ondelete="SET NULL"), nullable=True
    )

    # редактируемые
    grade: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skills: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    work_city: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    work_format: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_zone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # контакты
    work_phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    personal_phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    messengers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # даты/стаж
    birth_day: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    birth_month: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    experience_months: Mapped[Optional[int]] = mapped_column(nullable=True)

    # фото
    photo_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("media.id", ondelete="SET NULL"), nullable=True
    )

    # слепок внешних данных
    last_applied_snapshot_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("external_entity_snapshot.id", ondelete="SET NULL"),
        nullable=True,
    )

    # аутентификация/доступ
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # FTS STORED
    search_tsv: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('russian', coalesce(first_name,'')),'A') || "
            "setweight(to_tsvector('russian', coalesce(last_name,'')),'A')  || "
            "setweight(to_tsvector('russian', coalesce(title,'')),'B')      || "
            "setweight(to_tsvector('russian', coalesce(grade,'')),'C')      || "
            "setweight(to_tsvector('russian', coalesce(bio,'')),'D')        || "
            "setweight(to_tsvector('russian', coalesce(skills::text,'')),'C')",
            persisted=True,
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # relationships
    manager: Mapped[Optional["Employee"]] = relationship(
        remote_side="Employee.id", back_populates="subordinates"
    )
    subordinates: Mapped[List["Employee"]] = relationship(
        back_populates="manager"
    )

    primary_org_unit: Mapped[Optional["OrgUnit"]] = relationship(
        back_populates="employees", foreign_keys=[primary_org_unit_id]
    )

    photo: Mapped[Optional["Media"]] = relationship()

    teams: Mapped[List["EmployeeTeam"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan", passive_deletes=True
    )

    moderated_photos: Mapped[List["PhotoModeration"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active','dismissed')", name="ck_employee_status"
        ),
        CheckConstraint(
            "work_format IS NULL OR work_format IN ('office','hybrid','remote')",
            name="ck_employee_work_format",
        ),
        CheckConstraint(
            "birth_day IS NULL OR (birth_day BETWEEN 1 AND 31)",
            name="ck_employee_birth_day",
        ),
        CheckConstraint(
            "birth_month IS NULL OR (birth_month BETWEEN 1 AND 12)",
            name="ck_employee_birth_month",
        ),
        CheckConstraint(
            "experience_months IS NULL OR experience_months >= 0",
            name="ck_employee_experience_months",
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
        Index("idx_employee_primary_org_unit_id", "primary_org_unit_id"),
        Index("idx_employee_status", "status"),
        Index(
            "idx_employee_search_tsv",
            "search_tsv",
            postgresql_using="gin",
        ),
    )
