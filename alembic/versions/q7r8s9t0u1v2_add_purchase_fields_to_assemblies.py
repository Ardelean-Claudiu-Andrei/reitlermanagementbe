"""add purchase fields to assemblies

Revision ID: q7r8s9t0u1v2
Revises: p6q7r8s9t0u1
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = 'q7r8s9t0u1v2'
down_revision: Union[str, None] = 'p6q7r8s9t0u1'
branch_labels = None
depends_on = None


def _existing_columns(table: str) -> set[str]:
    bind = op.get_bind()
    result = bind.execute(sa.text(f"SHOW COLUMNS FROM `{table}`"))
    return {row[0] for row in result}


def upgrade() -> None:
    existing = _existing_columns('assemblies')
    if 'requires_purchase' not in existing:
        op.add_column('assemblies', sa.Column('requires_purchase', sa.Boolean(), nullable=False, server_default=sa.false()))
    if 'purchase_supplier' not in existing:
        op.add_column('assemblies', sa.Column('purchase_supplier', sa.String(300), server_default=''))
    if 'purchase_price' not in existing:
        op.add_column('assemblies', sa.Column('purchase_price', sa.Float(), nullable=True))
    if 'purchase_agent_contact' not in existing:
        op.add_column('assemblies', sa.Column('purchase_agent_contact', sa.String(300), server_default=''))
    if 'purchase_details' not in existing:
        op.add_column('assemblies', sa.Column('purchase_details', sa.Text(), nullable=True))


def downgrade() -> None:
    existing = _existing_columns('assemblies')
    if 'purchase_details' in existing:
        op.drop_column('assemblies', 'purchase_details')
    if 'purchase_agent_contact' in existing:
        op.drop_column('assemblies', 'purchase_agent_contact')
    if 'purchase_price' in existing:
        op.drop_column('assemblies', 'purchase_price')
    if 'purchase_supplier' in existing:
        op.drop_column('assemblies', 'purchase_supplier')
    if 'requires_purchase' in existing:
        op.drop_column('assemblies', 'requires_purchase')
