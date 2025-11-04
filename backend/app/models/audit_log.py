from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    actor_employee_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="SET NULL"),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(Text, nullable=False)

    # Универсальная адресация объекта события
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    before: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    after: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    ip: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),   # ← важно: дефолт на стороне БД
    )

    # Явно фиксируем FK, чтобы избежать неоднозначности
    actor: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys=[actor_employee_id],
    )

    __table_args__ = (
        Index("idx_audit_log_created_at", "created_at"),
        Index("idx_audit_log_actor", "actor_employee_id"),
        Index("idx_audit_log_entity", "entity_type", "entity_id"),
        Index("idx_audit_log_actor_created_at", "actor_employee_id", "created_at"),
        Index("idx_audit_log_entity_created_at", "entity_type", "entity_id", "created_at"),
    )
