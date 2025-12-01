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
    """Задача синхронизации сотрудников."""

    __tablename__ = "sync_job"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    trigger: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
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


class SyncRecord(Base):
    """Запись журнала синхронизации одного сотрудника."""

    __tablename__ = "sync_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sync_job.id", ondelete="CASCADE"),
        nullable=False,
    )

    external_ref: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)

    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    job: Mapped["SyncJob"] = relationship(
        "SyncJob",
        back_populates="records",
    )

    __table_args__ = (
        CheckConstraint(
            "action IN ('create','update','archive')",
            name="ck_sync_record_action",
        ),
        CheckConstraint(
            "status IN ('applied','error')",
            name="ck_sync_record_status",
        ),
        Index("idx_sync_record_job_external", "job_id", "external_ref"),
        Index("idx_sync_record_job_id", "job_id"),
        Index("idx_sync_record_error_code", "error_code"),
    )
