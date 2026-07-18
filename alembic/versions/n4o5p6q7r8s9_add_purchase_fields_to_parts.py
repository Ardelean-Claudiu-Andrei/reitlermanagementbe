"""add purchase fields to parts

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2026-07-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'n4o5p6q7r8s9'
down_revision: Union[str, None] = 'm3n4o5p6q7r8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_columns(table: str) -> set[str]:
    bind = op.get_bind()
    result = bind.execute(sa.text(f"SHOW COLUMNS FROM `{table}`"))
    return {row[0] for row in result}


def upgrade() -> None:
    existing = _existing_columns('parts')
    if 'requires_purchase' not in existing:
        op.add_column('parts', sa.Column('requires_purchase', sa.Boolean(), nullable=False, server_default=sa.false()))
    if 'purchase_supplier' not in existing:
        op.add_column('parts', sa.Column('purchase_supplier', sa.String(300), nullable=True, server_default=''))
    if 'purchase_price' not in existing:
        op.add_column('parts', sa.Column('purchase_price', sa.Float(), nullable=True))
    if 'purchase_agent_contact' not in existing:
        op.add_column('parts', sa.Column('purchase_agent_contact', sa.String(300), nullable=True, server_default=''))
    if 'purchase_details' not in existing:
        op.add_column('parts', sa.Column('purchase_details', sa.Text(), nullable=True))


def downgrade() -> None:
    existing = _existing_columns('parts')
    if 'purchase_details' in existing:
        op.drop_column('parts', 'purchase_details')
    if 'purchase_agent_contact' in existing:
        op.drop_column('parts', 'purchase_agent_contact')
    if 'purchase_price' in existing:
        op.drop_column('parts', 'purchase_price')
    if 'purchase_supplier' in existing:
        op.drop_column('parts', 'purchase_supplier')
    if 'requires_purchase' in existing:
        op.drop_column('parts', 'requires_purchase')
