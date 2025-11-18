"""remove exp_months ck and add new for hire_date

Revision ID: 2b476e8a5674
Revises: 3af2042bfbd7
Create Date: 2025-11-04 22:39:09.989653

"""
from typing import Sequence, Union

from alembic import op


revision: str = '2b476e8a5674'
down_revision: Union[str, Sequence[str], None] = '3af2042bfbd7'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE employee DROP CONSTRAINT IF EXISTS ck_employee_experience_nonneg"
    )

    op.execute(
        "ALTER TABLE employee DROP COLUMN IF EXISTS experience_months"
    )

    op.execute(
        "ALTER TABLE employee ADD COLUMN IF NOT EXISTS hire_date DATE"
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'ck_employee_hire_date_not_future'
            ) THEN
                ALTER TABLE employee
                ADD CONSTRAINT ck_employee_hire_date_not_future
                CHECK (hire_date <= CURRENT_DATE);
            END IF;
        END$$;
        """
    )


def downgrade():
    op.execute(
        "ALTER TABLE employee DROP CONSTRAINT IF EXISTS ck_employee_hire_date_not_future"
    )
    op.execute("ALTER TABLE employee DROP COLUMN IF EXISTS hire_date")
    op.execute(
        "ALTER TABLE employee ADD COLUMN IF NOT EXISTS experience_months INTEGER"
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'ck_employee_experience_nonneg'
            ) THEN
                ALTER TABLE employee
                ADD CONSTRAINT ck_employee_experience_nonneg
                CHECK ((experience_months IS NULL) OR (experience_months >= 0));
            END IF;
        END$$;
        """
    )