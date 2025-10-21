from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Team(Base):
    """Команда внутри орг-единицы."""

    __tablename__ = "team"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    org_unit_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("org_unit.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lead_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("employee.id", ondelete="SET NULL"), nullable=True
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    last_applied_snapshot_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("external_entity_snapshot.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # relationships
    org_unit: Mapped["OrgUnit"] = relationship(back_populates="teams")
    lead: Mapped[Optional["Employee"]] = relationship()
    members: Mapped[List["EmployeeTeam"]] = relationship(
        back_populates="team", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        Index("idx_team_org_unit_id", "org_unit_id"),
        Index(
            "idx_team_name_trgm",
            func.lower(name),
            postgresql_using="gin",
            postgresql_ops={func.lower(name).key: "gin_trgm_ops"},
        ),
    )
