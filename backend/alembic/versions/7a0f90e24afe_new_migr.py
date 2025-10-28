"""new_migr

Revision ID: 7a0f90e24afe
Revises: 898fabeadc21
Create Date: 2025-10-26 14:24:53.736848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a0f90e24afe'
down_revision: Union[str, Sequence[str], None] = '898fabeadc21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
