from __future__ import annotations

from datetime import datetime
from typing import Optional

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
    __tablename__ = "sync_job"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # 'scheduled' | 'manual'
    trigger: Mapped[str] = mapped_column(Text, nullable=False)

    # 'running' | 'success' | 'error' | 'partial'
    status: Mapped[str] = mapped_column(Text, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # произвольная агрегированная сводка по джобу
    summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

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
        CheckConstraint("trigger IN ('scheduled','manual')", name="ck_sync_job_trigger"),
        CheckConstraint("status IN ('running','success','error','partial')", name="ck_sync_job_status"),
        Index("idx_sync_job_started_at", "started_at"),
        Index("idx_sync_job_finished_at", "finished_at"),  # ← добавлено
        Index("idx_sync_job_status", "status"),
    )


class ExternalEntitySnapshot(Base):
    """
    Снапшот данных из внешнего источника (AD) по сотруднику.
    Теперь фиксируем только сотрудников; тип сущности не храним.
    """

    __tablename__ = "external_entity_snapshot"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # внешний идентификатор сотрудника в AD
    external_ref: Mapped[str] = mapped_column(Text, nullable=False)

    job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sync_job.id", ondelete="CASCADE"),
        nullable=False,
    )

    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    normalized: Mapped[dict] = mapped_column(JSONB, nullable=False)

    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    job: Mapped["SyncJob"] = relationship(back_populates="snapshots")

    __table_args__ = (
        # в рамках одного джоба один external_ref встречается не более одного раза
        Index("uq_ees_job_external_ref", "job_id", "external_ref", unique=True),
        # быстрый доступ к последнему снапшоту по сотруднику
        Index("idx_ees_external_ref_received", "external_ref", "received_at"),
    )


class SyncRecord(Base):
    """
    Журнал синхронизации сотрудников в рамках одного sync_job.

    Используется для:
      - фиксации create/update (status='applied')
      - фиксации orphaned (status='orphaned', action='archive')
      - фиксации ошибок связей (status='error')
      - последующего ручного решения по orphaned через decision
    """

    __tablename__ = "sync_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sync_job.id", ondelete="CASCADE"),
        nullable=False,
    )

    # внешний идентификатор сотрудника в AD
    external_ref: Mapped[str] = mapped_column(Text, nullable=False)

    # что хотели сделать: 'create' | 'update' | 'archive'
    action: Mapped[str] = mapped_column(Text, nullable=False)

    # результат: 'applied' | 'orphaned' | 'error'
    status: Mapped[str] = mapped_column(Text, nullable=False)

    # ручное решение по orphaned: NULL | 'archive' | 'keep'
    decision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    decided_by_employee_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="SET NULL"),
        nullable=True,
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # пояснение/ошибка
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # --- relationships ---
    job: Mapped["SyncJob"] = relationship("SyncJob", back_populates="records")
    decided_by: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys="SyncRecord.decided_by_employee_id",
    )

    __table_args__ = (
        CheckConstraint("action IN ('create','update','archive')", name="ck_sync_record_action"),
        CheckConstraint("status IN ('applied','orphaned','error')", name="ck_sync_record_status"),
        CheckConstraint("(decision IS NULL) OR (decision IN ('archive','keep'))", name="ck_sync_record_decision"),
        # быстрые выборки
        Index("idx_sync_record_job_external", "job_id", "external_ref"),
        Index("idx_sync_record_job_id", "job_id"),
    )
