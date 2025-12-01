"""Cleanup sync models and audit log.

Revision ID: 25467ca95595
Revises: a239db8c3750
Create Date: 2025-11-28 22:06:26.005749
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "25467ca95595"
down_revision: Union[str, Sequence[str], None] = "a239db8c3750"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    with op.batch_alter_table("employee") as batch_op:
        batch_op.drop_column("last_applied_snapshot_id")

    with op.batch_alter_table("sync_record") as batch_op:
        batch_op.drop_constraint("ck_sync_record_action", type_="check")
        batch_op.drop_constraint("ck_sync_record_status", type_="check")
        batch_op.drop_constraint("ck_sync_record_decision", type_="check")

        batch_op.drop_column("decision")
        batch_op.drop_column("decided_by_employee_id")
        batch_op.drop_column("decided_at")

        batch_op.add_column(sa.Column("error_code", sa.Text(), nullable=True))

        batch_op.create_check_constraint(
            "ck_sync_record_action",
            "action IN ('create','update')",
        )
        batch_op.create_check_constraint(
            "ck_sync_record_status",
            "status IN ('applied','error')",
        )

    op.create_index(
        "idx_sync_record_error_code",
        "sync_record",
        ["error_code"],
    )

    op.drop_table("external_entity_snapshot")
    op.drop_table("audit_log")


def downgrade() -> None:
    """Downgrade schema."""

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("actor_employee_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("before", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("after", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("ip", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "external_entity_snapshot",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("external_ref", sa.Text(), nullable=False),
        sa.Column(
            "job_id",
            sa.BigInteger(),
            sa.ForeignKey("sync_job.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("normalized", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.drop_index("idx_sync_record_error_code", table_name="sync_record")
    with op.batch_alter_table("sync_record") as batch_op:
        batch_op.drop_constraint("ck_sync_record_action", type_="check")
        batch_op.drop_constraint("ck_sync_record_status", type_="check")

        batch_op.drop_column("error_code")

        batch_op.add_column(sa.Column("decision", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("decided_by_employee_id", sa.BigInteger(), nullable=True),
        )
        batch_op.add_column(
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        )

        batch_op.create_check_constraint(
            "ck_sync_record_action",
            "action IN ('create','update','archive')",
        )
        batch_op.create_check_constraint(
            "ck_sync_record_status",
            "status IN ('applied','orphaned','error')",
        )
        batch_op.create_check_constraint(
            "ck_sync_record_decision",
            "(decision IS NULL) OR (decision IN ('archive','keep'))",
        )

    with op.batch_alter_table("employee") as batch_op:
        batch_op.add_column(
            sa.Column(
                "last_applied_snapshot_id",
                sa.BigInteger(),
                nullable=True,
            ),
        )
        batch_op.create_foreign_key(
            "employee_last_applied_snapshot_id_fkey",
            "external_entity_snapshot",
            ["last_applied_snapshot_id"],
            ["id"],
            ondelete="SET NULL",
        )
