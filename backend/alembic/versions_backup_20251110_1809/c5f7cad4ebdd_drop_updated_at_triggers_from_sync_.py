"""drop updated_at triggers from sync tables

Revision ID: c5f7cad4ebdd
Revises: 6456b9df07ab
Create Date: 2025-11-01 18:15:39.412255
"""

from typing import Sequence, Union
from alembic import op

revision: str = 'c5f7cad4ebdd'
down_revision: Union[str, Sequence[str], None] = '6456b9df07ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.execute("DROP TRIGGER IF EXISTS set_updated_at ON sync_job;")
    op.execute("DROP TRIGGER IF EXISTS set_updated_at ON sync_record;")
    op.execute("DROP TRIGGER IF EXISTS set_updated_at ON external_entity_snapshot;")

def downgrade():
    pass
