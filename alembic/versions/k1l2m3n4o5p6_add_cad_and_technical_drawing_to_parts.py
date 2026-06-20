"""add cad_location and technical_drawing_location to parts

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-06-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'k1l2m3n4o5p6'
down_revision: Union[str, None] = 'j0k1l2m3n4o5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('parts', sa.Column('cad_location', sa.String(500), nullable=True, server_default=''))
    op.add_column('parts', sa.Column('technical_drawing_location', sa.String(500), nullable=True, server_default=''))


def downgrade() -> None:
    op.drop_column('parts', 'technical_drawing_location')
    op.drop_column('parts', 'cad_location')
