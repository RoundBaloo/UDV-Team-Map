"""baseline: employee search extras (unaccent, STORED norm, trigram, clean FTS)"""

from alembic import op

# --- ВАЖНО: эти четыре строки должны быть ---
revision = "62210c465b44"
down_revision = None          # потому что создавали с --head base
branch_labels = None
depends_on = None
# --------------------------------------------

def upgrade():
    # 1) Расширения
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")

    # 2) Каноничный FTS-индекс на STORED tsvector
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = current_schema()
                  AND tablename  = 'employee'
                  AND indexname  = 'ix_employee_search_tsv'
            ) THEN
                EXECUTE 'CREATE INDEX ix_employee_search_tsv ON public.employee USING GIN (search_tsv)';
            END IF;
        END$$;
    """)

    # 3) Удалить возможный дубликат FTS-индекса
    op.execute("DROP INDEX IF EXISTS public.idx_employee_search_tsv;")

    # 4) STORED-колонка под триграммы
    op.execute("""
        ALTER TABLE public.employee
        ADD COLUMN IF NOT EXISTS search_text_norm text
          GENERATED ALWAYS AS (
            unaccent(lower(
              coalesce(first_name,'') || ' ' ||
              coalesce(middle_name,'') || ' ' ||
              coalesce(last_name,'') || ' ' ||
              coalesce(title,'') || ' ' ||
              coalesce(bio,'')
            ))
          ) STORED;
    """)

    # 5) Trigram-индекс
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_employee_search_text_norm_trgm
        ON public.employee
        USING GIN (search_text_norm gin_trgm_ops);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_employee_search_text_norm_trgm;")
    op.execute("ALTER TABLE public.employee DROP COLUMN IF EXISTS search_text_norm;")
    # Дубликатный idx_employee_search_tsv не восстанавливаем
