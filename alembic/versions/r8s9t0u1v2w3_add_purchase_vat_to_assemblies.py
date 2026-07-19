"""add purchase vat fields to assemblies

Revision ID: r8s9t0u1v2w3
Revises: q7r8s9t0u1v2
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = 'r8s9t0u1v2w3'
down_revision: Union[str, None] = 'q7r8s9t0u1v2'
branch_labels = None
depends_on = None


def _existing_columns(table: str) -> set[str]:
    bind = op.get_bind()
    result = bind.execute(sa.text(f"SHOW COLUMNS FROM `{table}`"))
    return {row[0] for row in result}


def upgrade() -> None:
    existing = _existing_columns('assemblies')
    if 'purchase_currency' not in existing:
        op.add_column('assemblies', sa.Column('purchase_currency', sa.String(10), server_default='EUR'))
    if 'purchase_vat_included' not in existing:
        op.add_column('assemblies', sa.Column('purchase_vat_included', sa.Boolean(), nullable=False, server_default=sa.false()))
    if 'purchase_vat_rate' not in existing:
        op.add_column('assemblies', sa.Column('purchase_vat_rate', sa.Float(), nullable=False, server_default='21'))


def downgrade() -> None:
    existing = _existing_columns('assemblies')
    if 'purchase_vat_rate' in existing:
        op.drop_column('assemblies', 'purchase_vat_rate')
    if 'purchase_vat_included' in existing:
        op.drop_column('assemblies', 'purchase_vat_included')
    if 'purchase_currency' in existing:
        op.drop_column('assemblies', 'purchase_currency')
