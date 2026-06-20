"""add step completion to projects

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa

revision = 'h8i9j0k1l2m3'
down_revision = 'g7h8i9j0k1l2'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE projects ADD COLUMN steps_completed JSON NULL")
    op.execute("ALTER TABLE projects ADD COLUMN steps_total INT NOT NULL DEFAULT 0")


def downgrade():
    op.execute("ALTER TABLE projects DROP COLUMN steps_total")
    op.execute("ALTER TABLE projects DROP COLUMN steps_completed")
