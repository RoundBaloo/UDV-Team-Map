"""Базовая миграция для поиска по сотрудникам (FTS, unaccent, триграммы)."""

from alembic import op

revision = "62210c465b44"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавляет расширения, FTS-индекс и STORED-колонку под триграммы."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = current_schema()
                  AND tablename  = 'employee'
                  AND indexname  = 'ix_employee_search_tsv'
            ) THEN
                EXECUTE
                    'CREATE INDEX ix_employee_search_tsv '
                    'ON public.employee USING GIN (search_tsv)';
            END IF;
        END$$;
        """
    )

    op.execute("DROP INDEX IF EXISTS public.idx_employee_search_tsv;")

    op.execute(
        """
        ALTER TABLE public.employee
        ADD COLUMN IF NOT EXISTS search_text_norm text
          GENERATED ALWAYS AS (
            unaccent(
              lower(
                coalesce(first_name, '') || ' ' ||
                coalesce(middle_name, '') || ' ' ||
                coalesce(last_name, '') || ' ' ||
                coalesce(title, '') || ' ' ||
                coalesce(bio, '')
              )
            )
          ) STORED;
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_employee_search_text_norm_trgm
        ON public.employee
        USING GIN (search_text_norm gin_trgm_ops);
        """
    )


def downgrade() -> None:
    """Удаляет триграммный индекс и STORED-колонку."""
    op.execute("DROP INDEX IF EXISTS idx_employee_search_text_norm_trgm;")
    op.execute("ALTER TABLE public.employee DROP COLUMN IF EXISTS search_text_norm;")
    # Индекс idx_employee_search_tsv не восстанавливается
