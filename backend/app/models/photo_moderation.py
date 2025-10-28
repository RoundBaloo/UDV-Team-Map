from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PhotoModeration(Base):
    """Модерация аватарок сотрудника HR-ом.

    Облегчённая версия без relationship, чтобы не ломать маппинг при синхронизации.
    """

    __tablename__ = "photo_moderation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # чьё фото модерируем
    employee_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="CASCADE"),
        nullable=False,
    )

    # какая медиа модерируется
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

    # кто проверил (HR / модератор)
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
        # индекс, который мы создаём в reset_db (status = 'pending')
        Index(
            "idx_photo_moderation_pending",
            "status",
            postgresql_where=(Text("status") == "pending"),  # декоративно, не критично
        ),
    )
