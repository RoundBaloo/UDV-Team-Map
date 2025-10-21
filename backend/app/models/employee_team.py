from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, PrimaryKeyConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EmployeeTeam(Base):
    """Связь сотрудник ↔ команда + роль и флаг основной команды."""

    __tablename__ = "employee_team"

    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employee.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("team.id", ondelete="CASCADE"), nullable=False
    )

    position_in_team: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    employee: Mapped["Employee"] = relationship(back_populates="teams")
    team: Mapped["Team"] = relationship(back_populates="members")

    __table_args__ = (
        PrimaryKeyConstraint("employee_id", "team_id"),
        Index("idx_employee_team_team_id", "team_id"),
        Index("idx_employee_team_employee_id", "employee_id"),
        # частично-уникальный: только для is_primary = true
        # (SQLAlchemy не умеет частичные UniqueConstraint декларативно — оставим в DDL/миграции)
    )
