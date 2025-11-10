from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    Computed,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Employee(Base):
    """Сотрудник компании."""

    __tablename__ = "employee"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # внешний идентификатор из AD (для отслеживания изменений)
    external_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Email, регистронезависимый (CITEXT)
    email: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True)

    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)

    # Должность
    title: Mapped[str] = mapped_column(Text, nullable=False)

    # active / dismissed
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="active",
    )

    # менеджер (руководитель сотрудника)
    manager_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="SET NULL"),
        nullable=True,
    )

    # мельчайший орг-юнит, к которому относится сотрудник
    lowest_org_unit_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("org_unit.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Био (интересы + о себе)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSONB { "python": 4, "fastapi": 3, ... }
    skill_ratings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Дополнительные рабочие поля
    work_city: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    work_format: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_zone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    work_phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mattermost_handle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    photo_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("media.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Ссылка на последний снапшот из AD
    last_applied_snapshot_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("external_entity_snapshot.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Авторизация / блокировки
    password_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    # STORED FTS
    search_tsv: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            text("""
                setweight(to_tsvector('russian', coalesce(first_name,'')),  'A') ||
                setweight(to_tsvector('russian', coalesce(middle_name,'')), 'A') ||
                setweight(to_tsvector('russian', coalesce(last_name,'')),   'A') ||
                setweight(to_tsvector('russian', coalesce(title,'')),       'B') ||
                setweight(to_tsvector('russian', coalesce(bio,'')),         'D')
            """),
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

    lowest_org_unit: Mapped[Optional["OrgUnit"]] = relationship(
        "OrgUnit", foreign_keys="Employee.lowest_org_unit_id", back_populates="employees"
    )

    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        remote_side="Employee.id",
        foreign_keys="Employee.manager_id",
    )

    search_text_norm: Mapped[str | None] = mapped_column(
    Text,
    Computed(text("""
        unaccent(lower(
          coalesce(first_name,'') || ' ' ||
          coalesce(middle_name,'') || ' ' ||
          coalesce(last_name,'') || ' ' ||
          coalesce(title,'') || ' ' ||
          coalesce(bio,'')
        ))
    """), persisted=True),
    nullable=True,
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
        CheckConstraint(
            "hire_date <= CURRENT_DATE",
            name="ck_employee_hire_date_not_future",
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
        Index("idx_employee_lowest_org_unit_id", "lowest_org_unit_id"),
        Index("idx_employee_status", "status"),
        Index("idx_employee_search_tsv", "search_tsv", postgresql_using="gin"),
        Index("idx_employee_skill_ratings", "skill_ratings", postgresql_using="gin"),
    )
