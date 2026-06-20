"""add drawing and CAD locations to assemblies

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-06-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'l2m3n4o5p6q7'
down_revision: Union[str, None] = 'k1l2m3n4o5p6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('assemblies', sa.Column('welding_drawing_location', sa.String(500), nullable=True, server_default=''))
    op.add_column('assemblies', sa.Column('technical_drawing_location', sa.String(500), nullable=True, server_default=''))
    op.add_column('assemblies', sa.Column('cad_location', sa.String(500), nullable=True, server_default=''))


def downgrade() -> None:
    op.drop_column('assemblies', 'cad_location')
    op.drop_column('assemblies', 'technical_drawing_location')
    op.drop_column('assemblies', 'welding_drawing_location')
