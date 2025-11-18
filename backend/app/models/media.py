from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Media(Base):
    """Медиа-файл в хранилище (например, фото-аватар сотрудника)."""

    __tablename__ = "media"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    storage_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index(
            "uq_media_storage_key",
            "storage_key",
            unique=True,
        ),
    )
