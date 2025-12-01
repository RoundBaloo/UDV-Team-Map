"""Org unit AD names and employee directions.

Revision ID: a180c95c5ff1
Revises: 01010b7e02be
Create Date: 2025-11-28 16:10:40.305268
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a180c95c5ff1"
down_revision: Union[str, Sequence[str], None] = "01010b7e02be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "org_unit",
        sa.Column("ad_name", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "idx_org_unit_parent_id_ad_name",
        "org_unit",
        ["parent_id", "ad_name"],
    )

    op.drop_constraint(
        "fk_employee_lowest_org_unit_id_org_unit",
        "employee",
        type_="foreignkey",
    )
    op.alter_column(
        "employee",
        "lowest_org_unit_id",
        new_column_name="department_id",
        existing_type=sa.BigInteger(),
        existing_nullable=True,
    )
    op.create_index(
        "idx_employee_department_id",
        "employee",
        ["department_id"],
    )
    op.create_foreign_key(
        "fk_employee_department_id_org_unit",
        "employee",
        "org_unit",
        ["department_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "employee",
        sa.Column("direction_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "idx_employee_direction_id",
        "employee",
        ["direction_id"],
    )
    op.create_foreign_key(
        "fk_employee_direction_id_org_unit",
        "employee",
        "org_unit",
        ["direction_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "fk_employee_direction_id_org_unit",
        "employee",
        type_="foreignkey",
    )
    op.drop_index(
        "idx_employee_direction_id",
        table_name="employee",
    )
    op.drop_column("employee", "direction_id")

    op.drop_constraint(
        "fk_employee_department_id_org_unit",
        "employee",
        type_="foreignkey",
    )
    op.drop_index(
        "idx_employee_department_id",
        table_name="employee",
    )
    op.alter_column(
        "employee",
        "department_id",
        new_column_name="lowest_org_unit_id",
        existing_type=sa.BigInteger(),
        existing_nullable=True,
    )
    op.create_index(
        "idx_employee_lowest_org_unit_id",
        "employee",
        ["lowest_org_unit_id"],
    )
    op.create_foreign_key(
        "fk_employee_lowest_org_unit_id_org_unit",
        "employee",
        "org_unit",
        ["lowest_org_unit_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_index(
        "idx_org_unit_parent_id_ad_name",
        table_name="org_unit",
    )
    op.drop_column("org_unit", "ad_name")
