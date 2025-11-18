"""Добавление employee.search_text_norm + триграммного индекса.

Revision ID: 13f3fe5f7e88
Revises: 62210c465b44
Create Date: 2025-11-10 21:32:12.276725
"""

from alembic import op

revision = "13f3fe5f7e88"
down_revision = "62210c465b44"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавляет нормализованное поле поиска и триграммный индекс."""
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.immutable_unaccent(text)
        RETURNS text
        LANGUAGE sql
        IMMUTABLE
        PARALLEL SAFE
        AS $$
            SELECT public.unaccent('public.unaccent', $1)
        $$;
        """
    )

    op.execute(
        """
        ALTER TABLE public.employee
        ADD COLUMN IF NOT EXISTS search_text_norm text
        GENERATED ALWAYS AS (
            public.immutable_unaccent(
                lower(
                    coalesce(first_name, '') || ' ' ||
                    coalesce(middle_name, '') || ' ' ||
                    coalesce(last_name, '') || ' ' ||
                    coalesce(title, '') || ' ' ||
                    coalesce(bio, '')
                )
            )
        ) STORED
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_employee_search_text_norm_trgm
        ON public.employee
        USING gin (search_text_norm gin_trgm_ops)
        """
    )


def downgrade() -> None:
    """Удаляет триграммный индекс и STORED-колонку."""
    op.execute("DROP INDEX IF EXISTS idx_employee_search_text_norm_trgm;")
    op.execute("ALTER TABLE public.employee DROP COLUMN IF EXISTS search_text_norm;")
