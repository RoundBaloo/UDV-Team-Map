from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Team(Base):
    __tablename__ = "team"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    external_ref: Mapped[Optional[str]] = mapped_column(
        Text,
        unique=True,
        nullable=True,
    )

    org_unit_id: Mapped[Optional[int]] = mapped_column(
    BigInteger,
    ForeignKey("org_unit.id", ondelete="SET NULL"),
    nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    lead_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("employee.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    last_applied_snapshot_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("external_entity_snapshot.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    org_unit: Mapped["OrgUnit"] = relationship(
        "OrgUnit",
        back_populates="teams",
        foreign_keys="Team.org_unit_id",
    )

    lead: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        foreign_keys="Team.lead_id",
    )

    member_links: Mapped[List["EmployeeTeam"]] = relationship(
        "EmployeeTeam",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "is_archived IN (false, true)",
            name="ck_team_is_archived_bool",
        ),
        Index("idx_team_org_unit_id", "org_unit_id"),
        Index("idx_team_lead_id", "lead_id"),
        Index(
            "idx_team_name_trgm",
            func.lower(name),
            postgresql_using="gin",
            postgresql_ops={func.lower(name).key: "gin_trgm_ops"},
        ),
    )
