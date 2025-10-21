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
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class OrgUnit(Base):
    """Блок/Отдел/Направление (иерархия)."""

    __tablename__ = "org_unit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("org_unit.id", ondelete="SET NULL"), nullable=True
    )

    unit_type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True)
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
    parent: Mapped[Optional["OrgUnit"]] = relationship(
        remote_side="OrgUnit.id", back_populates="children"
    )
    children: Mapped[List["OrgUnit"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan", passive_deletes=True
    )

    teams: Mapped[List["Team"]] = relationship(  # noqa: F821 (Team defined later)
        back_populates="org_unit", passive_deletes=True
    )

    __table_args__ = (
        CheckConstraint(
            "unit_type IN ('block','department','direction')",
            name="ck_org_unit_unit_type",
        ),
        # триграммный индекс на lower(name)
        Index(
            "idx_org_unit_name_trgm",
            func.lower(name),
            postgresql_using="gin",
            postgresql_ops={func.lower(name).key: "gin_trgm_ops"},
        ),
        Index("idx_org_unit_parent_id", "parent_id"),
    )
