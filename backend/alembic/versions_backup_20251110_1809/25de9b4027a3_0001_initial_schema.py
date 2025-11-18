"""0001_initial_schema

Revision ID: 25de9b4027a3
Revises:
Create Date: 2025-10-31 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "25de9b4027a3"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # 1.1 sync_job
    op.create_table(
        "sync_job",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "trigger",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("summary", postgresql.JSONB, nullable=True),
        sa.CheckConstraint(
            "trigger IN ('scheduled','manual')", name="ck_sync_job_trigger"
        ),
        sa.CheckConstraint(
            "status IN ('running','success','error','partial')",
            name="ck_sync_job_status",
        ),
    )
    op.create_index("idx_sync_job_started_at", "sync_job", ["started_at"])
    op.create_index("idx_sync_job_status", "sync_job", ["status"])

    # 1.2 external_entity_snapshot (ссылается на sync_job) — нужно ДО employee/org_unit
    op.create_table(
        "external_entity_snapshot",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("external_ref", sa.Text(), nullable=False),
        sa.Column(
            "job_id",
            sa.BigInteger(),
            sa.ForeignKey("sync_job.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("normalized", postgresql.JSONB, nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("local_id", sa.BigInteger(), nullable=True),
        sa.CheckConstraint(
            "entity_type IN ('employee','team','org_unit')",
            name="ck_ees_entity_type",
        ),
    )
    op.create_index(
        "idx_ees_entity_ext",
        "external_entity_snapshot",
        ["entity_type", "external_ref"],
    )
    op.create_index(
        "idx_ees_entity_local_received",
        "external_entity_snapshot",
        ["entity_type", "local_id", "received_at"],
    )

    # 1.3 media — до employee
    op.create_table(
        "media",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # 1.4 org_unit — БЕЗ FK на employee.manager_id (добавим позже ALTER'ом)
    op.create_table(
        "org_unit",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "parent_id",
            sa.BigInteger(),
            sa.ForeignKey("org_unit.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("unit_type", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("manager_id", sa.BigInteger(), nullable=True),  # FK later
        sa.Column(
            "last_applied_snapshot_id",
            sa.BigInteger(),
            sa.ForeignKey("external_entity_snapshot.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "unit_type IN ('group','domain','legal_entity','department','direction')",
            name="ck_org_unit_unit_type",
        ),
    )
    op.create_index("idx_org_unit_parent_id", "org_unit", ["parent_id"])
    # триграмм по name (lower)
    op.execute(
        "CREATE INDEX idx_org_unit_name_trgm ON org_unit USING GIN (lower(name) gin_trgm_ops)"
    )

    # 1.5 employee — теперь все внешние таблицы уже есть
    op.create_table(
        "employee",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("external_ref", sa.Text(), nullable=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False, unique=True),
        sa.Column("first_name", sa.Text(), nullable=False),
        sa.Column("middle_name", sa.Text(), nullable=True),
        sa.Column("last_name", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'active'")),
        sa.Column(
            "manager_id",
            sa.BigInteger(),
            sa.ForeignKey("employee.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "lowest_org_unit_id",
            sa.BigInteger(),
            sa.ForeignKey("org_unit.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("skill_ratings", postgresql.JSONB, nullable=True),
        sa.Column("work_city", sa.Text(), nullable=True),
        sa.Column(
            "work_format",
            sa.Text(),
            nullable=True,
        ),
        sa.Column("time_zone", sa.Text(), nullable=True),
        sa.Column("work_phone", sa.Text(), nullable=True),
        sa.Column("mattermost_handle", sa.Text(), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("experience_months", sa.Integer(), nullable=True),
        sa.Column(
            "photo_id",
            sa.BigInteger(),
            sa.ForeignKey("media.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "last_applied_snapshot_id",
            sa.BigInteger(),
            sa.ForeignKey("external_entity_snapshot.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "search_tsv",
            postgresql.TSVECTOR(),
            sa.Computed(
                sa.text(
                    """
            setweight(to_tsvector('russian', coalesce(first_name,'')),  'A') ||
            setweight(to_tsvector('russian', coalesce(middle_name,'')), 'A') ||
            setweight(to_tsvector('russian', coalesce(last_name,'')),   'A') ||
            setweight(to_tsvector('russian', coalesce(title,'')),       'B') ||
            setweight(to_tsvector('russian', coalesce(bio,'')),         'D')
                    """
                ),
                persisted=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('active','dismissed')", name="ck_employee_status"
        ),
        sa.CheckConstraint(
            "(work_format IS NULL) OR (work_format IN ('office','hybrid','remote'))",
            name="ck_employee_work_format",
        ),
        sa.CheckConstraint(
            "(experience_months IS NULL) OR (experience_months >= 0)",
            name="ck_employee_experience_nonneg",
        ),
    )
    op.create_index(
        "idx_employee_last_name_trgm",
        "employee",
        [sa.text("lower(last_name)")],
        postgresql_using="gin",
        postgresql_ops={"lower(last_name)": "gin_trgm_ops"},
    )
    op.create_index(
        "idx_employee_title_trgm",
        "employee",
        [sa.text("lower(title)")],
        postgresql_using="gin",
        postgresql_ops={"lower(title)": "gin_trgm_ops"},
    )
    op.create_index("idx_employee_manager_id", "employee", ["manager_id"])
    op.create_index("idx_employee_status", "employee", ["status"])
    op.create_index(
        "idx_employee_search_tsv",
        "employee",
        ["search_tsv"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "idx_employee_skill_ratings",
        "employee",
        ["skill_ratings"],
        unique=False,
        postgresql_using="gin",
    )

    # 1.6 зависимые таблицы от employee/media
    op.create_table(
        "photo_moderation",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "employee_id",
            sa.BigInteger(),
            sa.ForeignKey("employee.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "media_id",
            sa.BigInteger(),
            sa.ForeignKey("media.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("reviewer_employee_id", sa.BigInteger(), sa.ForeignKey("employee.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected')",
            name="ck_photo_moderation_status",
        ),
    )
    op.execute(
        "CREATE INDEX idx_photo_moderation_pending ON photo_moderation (status) WHERE status = 'pending'"
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("actor_employee_id", sa.BigInteger(), sa.ForeignKey("employee.id", ondelete="SET NULL")),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("before", postgresql.JSONB, nullable=True),
        sa.Column("after", postgresql.JSONB, nullable=True),
        sa.Column("ip", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_audit_log_created_at", "audit_log", ["created_at"])
    op.create_index("idx_audit_log_actor", "audit_log", ["actor_employee_id"])
    op.create_index("idx_audit_log_entity", "audit_log", ["entity_type", "entity_id"])

    op.create_table(
        "sync_record",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("job_id", sa.BigInteger(), sa.ForeignKey("sync_job.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_ref", sa.Text(), nullable=False),
        sa.Column("local_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("decided_by_employee_id", sa.BigInteger(), sa.ForeignKey("employee.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("action IN ('create','update','archive')", name="ck_sync_record_action"),
        sa.CheckConstraint("status IN ('applied','orphaned','error')", name="ck_sync_record_status"),
        sa.CheckConstraint("(decision IS NULL) OR (decision IN ('archive','keep'))", name="ck_sync_record_decision"),
    )
    op.create_index("idx_sync_record_entity_local", "sync_record", ["local_id"])
    op.create_index("idx_sync_record_job_id", "sync_record", ["job_id"])

    # --- 2) resolve the org_unit <-> employee cycle: add FK after both exist ---
    op.create_foreign_key(
        "org_unit_manager_fk",
        "org_unit",
        "employee",
        ["manager_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_org_unit_manager_id", "org_unit", ["manager_id"])


def downgrade() -> None:
    # порядок обратный

    op.drop_index("idx_org_unit_manager_id", table_name="org_unit")
    op.drop_constraint("org_unit_manager_fk", "org_unit", type_="foreignkey")

    op.drop_index("idx_sync_record_job_id", table_name="sync_record")
    op.drop_index("idx_sync_record_entity_local", table_name="sync_record")
    op.drop_table("sync_record")

    op.drop_index("idx_audit_log_entity", table_name="audit_log")
    op.drop_index("idx_audit_log_actor", table_name="audit_log")
    op.drop_index("idx_audit_log_created_at", table_name="audit_log")
    op.drop_table("audit_log")

    op.execute("DROP INDEX IF EXISTS idx_photo_moderation_pending")
    op.drop_table("photo_moderation")

    op.drop_index("idx_employee_skill_ratings", table_name="employee")
    op.drop_index("idx_employee_search_tsv", table_name="employee")
    op.drop_index("idx_employee_status", table_name="employee")
    op.drop_index("idx_employee_manager_id", table_name="employee")
    op.drop_index("idx_employee_title_trgm", table_name="employee")
    op.drop_index("idx_employee_last_name_trgm", table_name="employee")
    op.drop_table("employee")

    op.execute("DROP INDEX IF EXISTS idx_org_unit_name_trgm")
    op.drop_index("idx_org_unit_parent_id", table_name="org_unit")
    op.drop_table("org_unit")

    op.drop_table("media")

    op.drop_index("idx_ees_entity_local_received", table_name="external_entity_snapshot")
    op.drop_index("idx_ees_entity_ext", table_name="external_entity_snapshot")
    op.drop_table("external_entity_snapshot")

    op.drop_index("idx_sync_job_status", table_name="sync_job")
    op.drop_index("idx_sync_job_started_at", table_name="sync_job")
    op.drop_table("sync_job")
