"""add product quantities and project installation cost

Revision ID: a1b2c3d4e5f6
Revises: f5a6b7c8d9e0
Create Date: 2026-06-11 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Product: new quantity-aware assembly/part relations
    op.add_column('products', sa.Column('product_assemblies', sa.JSON(), nullable=True))
    op.add_column('products', sa.Column('product_parts', sa.JSON(), nullable=True))

    # Project: installation cost carried over from quote
    op.add_column('projects', sa.Column('installation_cost', sa.Float(), nullable=True, server_default='0'))


def downgrade() -> None:
    op.drop_column('products', 'product_assemblies')
    op.drop_column('products', 'product_parts')
    op.drop_column('projects', 'installation_cost')
