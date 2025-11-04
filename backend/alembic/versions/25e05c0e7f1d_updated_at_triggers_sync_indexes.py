"""updated_at triggers + sync indexes

Revision ID: a1b2c3d4e5f6
Revises: 25de9b4027a3
Create Date: 2025-11-01 12:34:56.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "25de9b4027a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    tables = [
        "employee",
        "org_unit",
        "media",
        "photo_moderation",
        "sync_job",
        "sync_record",
        "external_entity_snapshot",
        "audit_log",
        "sync_record",
    ]
    for t in set(tables):
        op.execute(
            f"""
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_trigger
                WHERE tgname = 'trg_set_updated_at_{t}'
              ) THEN
                CREATE TRIGGER trg_set_updated_at_{t}
                BEFORE UPDATE ON {t}
                FOR EACH ROW
                EXECUTE FUNCTION set_updated_at();
              END IF;
            END$$;
            """
        )

    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = 'ix_employee_external_ref'
              AND n.nspname = 'public'
          ) THEN
            CREATE INDEX ix_employee_external_ref ON employee (external_ref);
          END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = 'ix_org_unit_active_name_type'
              AND n.nspname = 'public'
          ) THEN
            CREATE INDEX ix_org_unit_active_name_type
            ON org_unit (name, unit_type)
            WHERE is_archived = false;
          END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = 'ix_employee_search_tsv'
              AND n.nspname = 'public'
          ) THEN
            CREATE INDEX ix_employee_search_tsv
            ON employee USING GIN (search_tsv);
          END IF;
        END$$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_employee_search_tsv;")
    op.execute("DROP INDEX IF EXISTS ix_org_unit_active_name_type;")
    op.execute("DROP INDEX IF EXISTS ix_employee_external_ref;")

    tables = [
        "employee",
        "org_unit",
        "media",
        "photo_moderation",
        "sync_job",
        "sync_record",
        "external_entity_snapshot",
        "audit_log",
    ]
    for t in set(tables):
        op.execute(f"DROP TRIGGER IF EXISTS trg_set_updated_at_{t} ON {t};")

    op.execute(
        """
        DO $$
        BEGIN
          -- если нет ни одного привязанного триггера, удалим функцию
          IF NOT EXISTS (
            SELECT 1 FROM pg_trigger
            WHERE tgfoid = (SELECT oid FROM pg_proc WHERE proname = 'set_updated_at')
              AND tgenabled <> 'D'
          ) THEN
            DROP FUNCTION IF EXISTS set_updated_at();
          END IF;
        END$$;
        """
    )
