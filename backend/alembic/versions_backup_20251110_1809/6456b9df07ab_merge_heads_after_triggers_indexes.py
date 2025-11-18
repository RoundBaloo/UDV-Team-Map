"""merge heads after triggers/indexes

Revision ID: 6456b9df07ab
Revises: 0813816b6ca6, a1b2c3d4e5f6
Create Date: 2025-11-01 17:11:11.982713

"""
from typing import Sequence, Union

revision: str = '6456b9df07ab'
down_revision: Union[str, Sequence[str], None] = ('0813816b6ca6', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
