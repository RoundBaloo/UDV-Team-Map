"""add_employee_telegram_handle

Revision ID: 01010b7e02be
Revises: 13f3fe5f7e88
Create Date: 2025-11-22 13:44:30.890195

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '01010b7e02be'
down_revision: Union[str, Sequence[str], None] = '13f3fe5f7e88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employee",
        sa.Column("telegram_handle", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("employee", "telegram_handle")