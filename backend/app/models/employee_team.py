from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EmployeeTeam(Base):
    __tablename__ = "employee_team"

    # составной первичный ключ (employee_id + team_id)
    employee_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="CASCADE"),
        primary_key=True,
    )

    team_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("team.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # роль/позиция в команде
    position_in_team: Mapped[str | None] = mapped_column(Text, nullable=True)

    # флаг "это основная команда сотрудника?"
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    # никаких created_at тут не указываем, потому что физически в таблице её нет

    # ORM-связи
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="team_links",
    )

    team: Mapped["Team"] = relationship(
        "Team",
        back_populates="member_links",
    )
