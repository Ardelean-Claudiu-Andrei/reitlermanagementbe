"""add new models: parts, assemblies, quotes, projects, inventory; rework products

Revision ID: b1c2d3e4f5a6
Revises: 6db9ccc781f5
Create Date: 2026-03-29 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = '6db9ccc781f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop tables that depend on products first
    op.drop_table('offer_items')
    op.drop_table('stock_movements')
    op.drop_table('products')

    # Recreate products with new schema
    op.create_table('products',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.JSON(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False, server_default='other'),
        sa.Column('unit', sa.String(50), nullable=True, server_default='buc'),
        sa.Column('base_price', sa.Float(), nullable=False, server_default='0'),
        sa.Column('assembly_ids', sa.JSON(), nullable=True),
        sa.Column('part_ids', sa.JSON(), nullable=True),
        sa.Column('assembly_steps', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_products_code', 'products', ['code'], unique=True)

    # Recreate offer_items
    op.create_table('offer_items',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('offer_id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('discount_percent', sa.Float(), nullable=True),
        sa.Column('line_total', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['offer_id'], ['offers.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Recreate stock_movements
    op.create_table('stock_movements',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('type', sa.Enum('IN', 'OUT', 'ADJUSTMENT', name='movementtype'), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── Create parts table ───────────────────────────────────────────────────
    op.create_table('parts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.JSON(), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=True),
        sa.Column('file_location', sa.String(500), nullable=True),
        sa.Column('unit', sa.String(50), nullable=True, server_default='buc'),
        sa.Column('base_price', sa.Float(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── Create assemblies table ──────────────────────────────────────────────
    op.create_table('assemblies',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.JSON(), nullable=True),
        sa.Column('parts', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_assemblies_code', 'assemblies', ['code'], unique=True)

    # ── Create quotes table ──────────────────────────────────────────────────
    op.create_table('quotes',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('company_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('validity', sa.String(50), nullable=True),
        sa.Column('delivery_time_weeks', sa.Integer(), nullable=True, server_default='4'),
        sa.Column('items', sa.JSON(), nullable=True),
        sa.Column('installation', sa.Float(), nullable=True, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['clients.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── Create projects table ────────────────────────────────────────────────
    op.create_table('projects',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('company_id', sa.String(36), nullable=True),
        sa.Column('quote_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('start_date', sa.String(50), nullable=True),
        sa.Column('deadline', sa.String(50), nullable=True),
        sa.Column('finish_date', sa.String(50), nullable=True),
        sa.Column('warranty_expiration', sa.String(50), nullable=True),
        sa.Column('items', sa.JSON(), nullable=True),
        sa.Column('checklist', sa.JSON(), nullable=True),
        sa.Column('issues', sa.JSON(), nullable=True),
        sa.Column('activity', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['clients.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['quote_id'], ['quotes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_projects_code', 'projects', ['code'], unique=True)

    # ── Create inventory_items table ─────────────────────────────────────────
    op.create_table('inventory_items',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('item_id', sa.String(36), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=True, server_default='0'),
        sa.Column('min_stock', sa.Float(), nullable=True, server_default='0'),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('inventory_items')
    op.drop_index('ix_projects_code', table_name='projects')
    op.drop_table('projects')
    op.drop_table('quotes')
    op.drop_index('ix_assemblies_code', table_name='assemblies')
    op.drop_table('assemblies')
    op.drop_table('parts')
    op.drop_table('offer_items')
    op.drop_table('stock_movements')
    op.drop_index('ix_products_code', table_name='products')
    op.drop_table('products')

    # Restore original products table
    op.create_table('products',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('category_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sku', sa.String(100), nullable=True),
        sa.Column('price', sa.Float(), nullable=False, server_default='0'),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('stock_quantity', sa.Float(), nullable=True),
        sa.Column('min_stock_alert', sa.Float(), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_products_sku', 'products', ['sku'], unique=True)

    op.create_table('offer_items',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('offer_id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('discount_percent', sa.Float(), nullable=True),
        sa.Column('line_total', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['offer_id'], ['offers.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('stock_movements',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('type', sa.Enum('IN', 'OUT', 'ADJUSTMENT', name='movementtype'), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
