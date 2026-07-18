"""add purchase_vat_included and purchase_vat_rate to parts

Revision ID: p6q7r8s9t0u1
Revises: o5p6q7r8s9t0
Create Date: 2026-07-18 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'p6q7r8s9t0u1'
down_revision: Union[str, None] = 'o5p6q7r8s9t0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_columns(table: str) -> set[str]:
    bind = op.get_bind()
    result = bind.execute(sa.text(f"SHOW COLUMNS FROM `{table}`"))
    return {row[0] for row in result}


def upgrade() -> None:
    existing = _existing_columns('parts')
    if 'purchase_vat_included' not in existing:
        op.add_column('parts', sa.Column('purchase_vat_included', sa.Boolean(), nullable=False, server_default=sa.false()))
    if 'purchase_vat_rate' not in existing:
        op.add_column('parts', sa.Column('purchase_vat_rate', sa.Float(), nullable=False, server_default='21'))


def downgrade() -> None:
    existing = _existing_columns('parts')
    if 'purchase_vat_rate' in existing:
        op.drop_column('parts', 'purchase_vat_rate')
    if 'purchase_vat_included' in existing:
        op.drop_column('parts', 'purchase_vat_included')
