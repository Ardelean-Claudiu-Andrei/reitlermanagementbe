"""add final_price to projects

Revision ID: i9j0k1l2m3n4
Revises: f115cd7740cb
Create Date: 2026-06-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'i9j0k1l2m3n4'
down_revision: Union[str, None] = 'f115cd7740cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('final_price', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'final_price')
