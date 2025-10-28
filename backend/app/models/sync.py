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
    trigger: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    snapshots: Mapped[list["ExternalEntitySnapshot"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", passive_deletes=True
    )
    records: Mapped[list["SyncRecord"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        CheckConstraint(
            "trigger IN ('scheduled','manual')", name="ck_sync_job_trigger"
        ),
        CheckConstraint(
            "status IN ('running','success','error','partial')", name="ck_sync_job_status"
        ),
        Index("idx_sync_job_started_at", "started_at"),
        Index("idx_sync_job_status", "status"),
    )


class ExternalEntitySnapshot(Base):
    __tablename__ = "external_entity_snapshot"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    external_ref: Mapped[str] = mapped_column(Text, nullable=False)
    job_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sync_job.id", ondelete="CASCADE"), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    normalized: Mapped[dict] = mapped_column(JSONB, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    local_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    job: Mapped["SyncJob"] = relationship(back_populates="snapshots")

    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('employee','team','org_unit')",
            name="ck_ees_entity_type",
        ),
        Index("idx_ees_entity_ext", "entity_type", "external_ref"),
        Index(
            "idx_ees_entity_local_received", "entity_type", "local_id", "received_at"
        ),
    )


class SyncRecord(Base):
    """
    Журнал синхронизации сущностей (org_unit / team / employee)
    в рамках одного sync_job.

    Используется для:
    - фиксации create/update (status='applied')
    - фиксации orphaned (status='orphaned', action='archive')
    - фиксации ошибок связей (status='error')
    - последующего ручного решения по orphaned через decision.
    """

    __tablename__ = "sync_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sync_job.id", ondelete="CASCADE"),
        nullable=False,
    )

    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    external_ref: Mapped[str] = mapped_column(Text, nullable=False)

    # локальный ID созданной/обновлённой записи (employee.id / team.id / org_unit.id)
    local_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )

    # что мы хотели сделать с этой сущностью
    action: Mapped[str] = mapped_column(Text, nullable=False)

    # чем закончилось
    status: Mapped[str] = mapped_column(Text, nullable=False)

    # ручное решение по орфану (может быть None, если пока не решено)
    decision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    decided_by_employee_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="SET NULL"),
        nullable=True,
    )

    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # пояснение/ошибка
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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

    decided_by: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys="SyncRecord.decided_by_employee_id",
    )

    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('employee','team','org_unit')",
            name="ck_sync_record_entity_type",
        ),
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
        Index("idx_sync_record_entity_local", "entity_type", "local_id"),
        Index("idx_sync_record_job_id", "job_id"),
    )
