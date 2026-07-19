"""add purchase_currency to parts

Revision ID: o5p6q7r8s9t0
Revises: n4o5p6q7r8s9
Create Date: 2026-07-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'o5p6q7r8s9t0'
down_revision: Union[str, None] = 'n4o5p6q7r8s9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_columns(table: str) -> set[str]:
    bind = op.get_bind()
    result = bind.execute(sa.text(f"SHOW COLUMNS FROM `{table}`"))
    return {row[0] for row in result}


def upgrade() -> None:
    existing = _existing_columns('parts')
    if 'purchase_currency' not in existing:
        op.add_column('parts', sa.Column('purchase_currency', sa.String(10), nullable=True, server_default='EUR'))


def downgrade() -> None:
    existing = _existing_columns('parts')
    if 'purchase_currency' in existing:
        op.drop_column('parts', 'purchase_currency')
