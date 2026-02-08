"""Add deleted_flag to all tables for soft delete

Revision ID: 2f94c130cdf8
Revises: 3857dc264a04
Create Date: 2026-02-08 22:48:28.205696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f94c130cdf8'
down_revision: Union[str, Sequence[str], None] = '3857dc264a04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add deleted_flag to tables that don't have it
    op.add_column('users', sa.Column('deleted_flag', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('delivery_notes', sa.Column('deleted_flag', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('delivery_note_details', sa.Column('deleted_flag', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('sales_invoices', sa.Column('deleted_flag', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('sales_invoice_details', sa.Column('deleted_flag', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove deleted_flag from tables
    op.drop_column('sales_invoice_details', 'deleted_flag')
    op.drop_column('sales_invoices', 'deleted_flag')
    op.drop_column('delivery_note_details', 'deleted_flag')
    op.drop_column('delivery_notes', 'deleted_flag')
    op.drop_column('users', 'deleted_flag')
