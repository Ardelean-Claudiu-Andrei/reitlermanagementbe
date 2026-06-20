"""add engineer production roles

Revision ID: g7h8i9j0k1l2
Revises: f5a6b7c8d9e0
Create Date: 2026-06-15
"""
from alembic import op

revision = 'g7h8i9j0k1l2'
down_revision = 'f5a6b7c8d9e0'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE users MODIFY COLUMN role "
        "ENUM('ADMIN','USER','ENGINEER','PRODUCTION') NOT NULL DEFAULT 'USER'"
    )


def downgrade():
    # Revert any ENGINEER/PRODUCTION users to USER before shrinking the enum
    op.execute("UPDATE users SET role = 'USER' WHERE role IN ('ENGINEER','PRODUCTION')")
    op.execute(
        "ALTER TABLE users MODIFY COLUMN role "
        "ENUM('ADMIN','USER') NOT NULL DEFAULT 'USER'"
    )
