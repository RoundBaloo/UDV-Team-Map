"""ensure employee.search_text_norm + trigram index + extensions

Revision ID: 13f3fe5f7e88
Revises: 62210c465b44
Create Date: 2025-11-10 21:32:12.276725

"""
"""ensure employee.search_text_norm + trigram index + extensions"""

from alembic import op

# ⚠️ подставь свой revision из имени файла
revision = "13f3fe5f7e88"
down_revision = "62210c465b44"
branch_labels = None
depends_on = None


def upgrade():
    # 1) Расширения
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # 2) IMMUTABLE-обёртка над unaccent (иначе STORED-колонку создать нельзя)
    #   - важно квалифицировать словарь 'public.unaccent', иначе в некоторых сборках функция не IMMUTABLE
    op.execute("""
        CREATE OR REPLACE FUNCTION public.immutable_unaccent(text)
        RETURNS text
        LANGUAGE sql
        IMMUTABLE
        PARALLEL SAFE
        AS $$
            SELECT public.unaccent('public.unaccent', $1)
        $$;
    """)

    # 3) STORED-колонка с использованием IMMUTABLE-обёртки
    op.execute("""
        ALTER TABLE public.employee
        ADD COLUMN IF NOT EXISTS search_text_norm text
        GENERATED ALWAYS AS (
            public.immutable_unaccent(
                lower(
                    coalesce(first_name,'') || ' ' ||
                    coalesce(middle_name,'') || ' ' ||
                    coalesce(last_name,'') || ' ' ||
                    coalesce(title,'') || ' ' ||
                    coalesce(bio,'')
                )
            )
        ) STORED
    """)

    # 4) GIN-триграмм-индекс на нормализованной колонке
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_employee_search_text_norm_trgm
        ON public.employee
        USING gin (search_text_norm gin_trgm_ops)
    """)

def downgrade():
    # Откат: удаляем триграмм-индекс и STORED-колонку (расширения оставляем)
    op.execute("DROP INDEX IF EXISTS idx_employee_search_text_norm_trgm;")
    op.execute("ALTER TABLE public.employee DROP COLUMN IF EXISTS search_text_norm;")