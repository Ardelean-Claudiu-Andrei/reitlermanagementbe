"""merge_heads

Revision ID: f115cd7740cb
Revises: b2c3d4e5f6a7, h8i9j0k1l2m3
Create Date: 2026-06-18 00:58:37.607050

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f115cd7740cb'
down_revision: Union[str, None] = ('b2c3d4e5f6a7', 'h8i9j0k1l2m3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
