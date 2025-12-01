"""Check ORM sync.

Revision ID: a239db8c3750
Revises: a180c95c5ff1
Create Date: 2025-11-28 17:00:48.983848
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a239db8c3750"
down_revision: Union[str, Sequence[str], None] = "a180c95c5ff1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.alter_column(
        "org_unit",
        "ad_name",
        existing_type=sa.VARCHAR(length=255),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "org_unit",
        "ad_name",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=255),
        existing_nullable=True,
    )
