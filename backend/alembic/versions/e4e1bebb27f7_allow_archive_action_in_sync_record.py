"""Allow archive action in sync_record.

Revision ID: e4e1bebb27f7
Revises: 25467ca95595
Create Date: 2025-11-30 11:03:16.112921
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e4e1bebb27f7"
down_revision: Union[str, Sequence[str], None] = "25467ca95595"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.drop_constraint(
        "ck_sync_record_action",
        "sync_record",
        type_="check",
    )
    op.create_check_constraint(
        "ck_sync_record_action",
        "sync_record",
        "action IN ('create','update','archive')",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "ck_sync_record_action",
        "sync_record",
        type_="check",
    )
    op.create_check_constraint(
        "ck_sync_record_action",
        "sync_record",
        "action IN ('create','update')",
    )
