"""add purchase fields to products

Revision ID: s9t0u1v2w3x4
Revises: r8s9t0u1v2w3
Create Date: 2026-07-19

"""
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import false


revision: str = 's9t0u1v2w3x4'
down_revision: Union[str, None] = 'r8s9t0u1v2w3'
branch_labels = None
depends_on = None


def _existing_columns(connection, table_name: str) -> set:
    try:
        result = connection.execute(sa.text(f"SHOW COLUMNS FROM `{table_name}`"))
        return {row[0] for row in result}
    except Exception:
        return set()


def upgrade() -> None:
    existing = _existing_columns(op.get_bind(), "products")

    if "requires_purchase" not in existing:
        op.add_column("products", sa.Column("requires_purchase", sa.Boolean(), nullable=False, server_default=false()))
    if "purchase_supplier" not in existing:
        op.add_column("products", sa.Column("purchase_supplier", sa.String(300), server_default=""))
    if "purchase_price" not in existing:
        op.add_column("products", sa.Column("purchase_price", sa.Float(), nullable=True))
    if "purchase_currency" not in existing:
        op.add_column("products", sa.Column("purchase_currency", sa.String(10), server_default="EUR"))
    if "purchase_vat_included" not in existing:
        op.add_column("products", sa.Column("purchase_vat_included", sa.Boolean(), nullable=False, server_default=false()))
    if "purchase_vat_rate" not in existing:
        op.add_column("products", sa.Column("purchase_vat_rate", sa.Float(), server_default="21"))
    if "purchase_agent_contact" not in existing:
        op.add_column("products", sa.Column("purchase_agent_contact", sa.String(300), server_default=""))
    if "purchase_details" not in existing:
        op.add_column("products", sa.Column("purchase_details", sa.Text(), nullable=True))


def downgrade() -> None:
    existing = _existing_columns(op.get_bind(), "products")
    for col in [
        "purchase_details",
        "purchase_agent_contact",
        "purchase_vat_rate",
        "purchase_vat_included",
        "purchase_currency",
        "purchase_price",
        "purchase_supplier",
        "requires_purchase",
    ]:
        if col in existing:
            op.drop_column("products", col)
