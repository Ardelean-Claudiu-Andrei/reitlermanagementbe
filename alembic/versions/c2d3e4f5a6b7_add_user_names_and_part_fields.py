"""add first_name/last_name to users and extend parts with category/stock/location

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-03-29 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Add first_name / last_name to users ──────────────────────────────────
    op.add_column('users', sa.Column('first_name', sa.String(100), nullable=True, server_default=''))
    op.add_column('users', sa.Column('last_name', sa.String(100), nullable=True, server_default=''))

    # Populate first_name / last_name from existing name column (split on first space)
    op.execute("""
        UPDATE users
        SET
            first_name = TRIM(SUBSTRING_INDEX(name, ' ', 1)),
            last_name  = TRIM(SUBSTRING(name, LOCATE(' ', name) + 1))
        WHERE name IS NOT NULL AND name != ''
    """)

    # ── Extend parts with new fields ─────────────────────────────────────────
    op.add_column('parts', sa.Column('category', sa.String(100), nullable=True, server_default=''))
    op.add_column('parts', sa.Column('minimum_stock', sa.Float(), nullable=True, server_default='0'))
    op.add_column('parts', sa.Column('quantity', sa.Float(), nullable=True, server_default='0'))
    op.add_column('parts', sa.Column('location', sa.String(200), nullable=True, server_default=''))
    op.add_column('parts', sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('parts', 'notes')
    op.drop_column('parts', 'location')
    op.drop_column('parts', 'quantity')
    op.drop_column('parts', 'minimum_stock')
    op.drop_column('parts', 'category')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
