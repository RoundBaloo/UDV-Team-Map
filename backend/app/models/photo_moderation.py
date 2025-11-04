from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Text,
    CheckConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PhotoModeration(Base):
    """Модерация аватарок сотрудника HR-ом.

    Упрощённо: без relationship, чтобы не влиять на синхронизацию.
    """

    __tablename__ = "photo_moderation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # чей аватар модератор проверяет
    employee_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="CASCADE"),
        nullable=False,
    )

    # какая медиа проверяется
    media_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("media.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 'pending' | 'approved' | 'rejected'
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="pending",
    )

    # кто проверил (HR / модератор), может быть не задан, если pending
    reviewer_employee_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="SET NULL"),
        nullable=True,
    )

    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reject_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        # фиксируем допустимые значения статуса
        CheckConstraint(
            "status IN ('pending','approved','rejected')",
            name="ck_photo_moderation_status",
        ),

        # быстрый поиск всех pending
        Index("idx_photo_moderation_status", "status"),

        # быстрый поиск pending по сотруднику
        Index(
            "idx_photo_moderation_pending_emp",
            "employee_id",
            postgresql_where=text("status = 'pending'"),
        ),

        # не более ОДНОЙ pending-заявки на сотрудника
        Index(
            "uq_photo_moderation_one_pending_per_employee",
            "employee_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),

        # для аналитики/истории модераций по сотруднику/модератору
        Index("idx_photo_moderation_employee", "employee_id"),
        Index("idx_photo_moderation_reviewer", "reviewer_employee_id"),
        Index("idx_photo_moderation_created_at", "created_at"),
    )
