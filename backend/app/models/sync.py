from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SyncJob(Base):
    """Задача синхронизации (один запуск импорта из внешней системы)."""

    __tablename__ = "sync_job"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Источник запуска: scheduled / manual
    trigger: Mapped[str] = mapped_column(Text, nullable=False)

    # Статус выполнения: running / success / error / partial
    status: Mapped[str] = mapped_column(Text, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Агрегированная сводка по джобу
    summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    snapshots: Mapped[list["ExternalEntitySnapshot"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    records: Mapped[list["SyncRecord"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "trigger IN ('scheduled','manual')",
            name="ck_sync_job_trigger",
        ),
        CheckConstraint(
            "status IN ('running','success','error','partial')",
            name="ck_sync_job_status",
        ),
        Index("idx_sync_job_started_at", "started_at"),
        Index("idx_sync_job_finished_at", "finished_at"),
        Index("idx_sync_job_status", "status"),
    )


class ExternalEntitySnapshot(Base):
    """Снапшот данных из внешнего источника (AD) по сотруднику."""

    __tablename__ = "external_entity_snapshot"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Внешний идентификатор сотрудника в AD
    external_ref: Mapped[str] = mapped_column(Text, nullable=False)

    job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sync_job.id", ondelete="CASCADE"),
        nullable=False,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    normalized: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    job: Mapped["SyncJob"] = relationship(
        back_populates="snapshots",
    )

    __table_args__ = (
        # В рамках одного джоба один external_ref встречается не более одного раза
        Index(
            "uq_ees_job_external_ref",
            "job_id",
            "external_ref",
            unique=True,
        ),
        # Быстрый доступ к последнему снапшоту по сотруднику
        Index(
            "idx_ees_external_ref_received",
            "external_ref",
            "received_at",
        ),
    )


class SyncRecord(Base):
    """Журнал синхронизации сотрудников в рамках одного sync_job."""

    __tablename__ = "sync_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sync_job.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Внешний идентификатор сотрудника в AD
    external_ref: Mapped[str] = mapped_column(Text, nullable=False)

    # Действие: create / update / archive
    action: Mapped[str] = mapped_column(Text, nullable=False)

    # Результат: applied / orphaned / error
    status: Mapped[str] = mapped_column(Text, nullable=False)

    # Ручное решение по orphaned: NULL / archive / keep
    decision: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    decided_by_employee_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="SET NULL"),
        nullable=True,
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Пояснение / ошибка
    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # --- relationships ---

    job: Mapped["SyncJob"] = relationship(
        "SyncJob",
        back_populates="records",
    )
    decided_by: Mapped["Employee"] = relationship(
        "Employee",
        foreign_keys="SyncRecord.decided_by_employee_id",
    )

    __table_args__ = (
        CheckConstraint(
            "action IN ('create','update','archive')",
            name="ck_sync_record_action",
        ),
        CheckConstraint(
            "status IN ('applied','orphaned','error')",
            name="ck_sync_record_status",
        ),
        CheckConstraint(
            "(decision IS NULL) OR (decision IN ('archive','keep'))",
            name="ck_sync_record_decision",
        ),
        Index("idx_sync_record_job_external", "job_id", "external_ref"),
        Index("idx_sync_record_job_id", "job_id"),
    )
