from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PhotoModeration(Base):
    """Запись о модерации аватара сотрудника HR-ом."""

    __tablename__ = "photo_moderation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Сотрудник, чей аватар проверяется
    employee_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Проверяемый медиа-объект
    media_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("media.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Статус: pending / approved / rejected
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="pending",
    )

    # Кто проверил (HR / модератор), может быть не задан, если pending
    reviewer_employee_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="SET NULL"),
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reject_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        # Допустимые значения статуса
        CheckConstraint(
            "status IN ('pending','approved','rejected')",
            name="ck_photo_moderation_status",
        ),
        # Быстрый поиск по статусу
        Index("idx_photo_moderation_status", "status"),
        # Быстрый поиск pending по сотруднику
        Index(
            "idx_photo_moderation_pending_emp",
            "employee_id",
            postgresql_where=text("status = 'pending'"),
        ),
        # Не более одной pending-заявки на сотрудника
        Index(
            "uq_photo_moderation_one_pending_per_employee",
            "employee_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        # Аналитика/история модераций
        Index("idx_photo_moderation_employee", "employee_id"),
        Index("idx_photo_moderation_reviewer", "reviewer_employee_id"),
        Index("idx_photo_moderation_created_at", "created_at"),
    )
