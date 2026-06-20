"""add assembly part production fields and uploaded_files table

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-06-06 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f5a6b7c8d9e0'
down_revision: Union[str, None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- assemblies ---
    op.add_column('assemblies', sa.Column('composition_type', sa.String(50), nullable=True, server_default='standalone'))
    op.add_column('assemblies', sa.Column('physical_location', sa.String(300), nullable=True, server_default=''))
    op.add_column('assemblies', sa.Column('production_steps', sa.JSON(), nullable=True))

    # --- parts ---
    op.add_column('parts', sa.Column('code', sa.String(100), nullable=True))
    op.add_column('parts', sa.Column('drawing_location', sa.String(500), nullable=True, server_default=''))
    op.add_column('parts', sa.Column('required_quantity', sa.Integer(), nullable=True, server_default='1'))
    op.add_column('parts', sa.Column('physical_location', sa.String(300), nullable=True, server_default=''))
    op.add_column('parts', sa.Column('production_steps', sa.JSON(), nullable=True))
    op.add_column('parts', sa.Column('requires_laser_cutting', sa.Boolean(), nullable=True, server_default=sa.false()))
    op.add_column('parts', sa.Column('welding_drawing_location', sa.String(500), nullable=True, server_default=''))
    op.add_column('parts', sa.Column('bending_drawing_location', sa.String(500), nullable=True, server_default=''))
    op.create_index('ix_parts_code', 'parts', ['code'], unique=True)

    # --- products ---
    op.add_column('products', sa.Column('production_steps', sa.JSON(), nullable=True))

    # --- uploaded_files ---
    op.create_table(
        'uploaded_files',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('entity_type', sa.String(20), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('file_category', sa.String(50), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('stored_path', sa.String(500), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_uploaded_files_entity', 'uploaded_files', ['entity_type', 'entity_id'])


def downgrade() -> None:
    op.drop_index('ix_uploaded_files_entity', table_name='uploaded_files')
    op.drop_table('uploaded_files')

    op.drop_column('products', 'production_steps')

    op.drop_index('ix_parts_code', table_name='parts')
    op.drop_column('parts', 'bending_drawing_location')
    op.drop_column('parts', 'welding_drawing_location')
    op.drop_column('parts', 'requires_laser_cutting')
    op.drop_column('parts', 'production_steps')
    op.drop_column('parts', 'physical_location')
    op.drop_column('parts', 'required_quantity')
    op.drop_column('parts', 'drawing_location')
    op.drop_column('parts', 'code')

    op.drop_column('assemblies', 'production_steps')
    op.drop_column('assemblies', 'physical_location')
    op.drop_column('assemblies', 'composition_type')
