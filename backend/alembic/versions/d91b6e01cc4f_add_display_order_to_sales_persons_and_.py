"""add_display_order_to_sales_persons_and_contractors

Revision ID: d91b6e01cc4f
Revises: 4d5512e21ca0
Create Date: 2026-02-09 00:11:47.998487

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd91b6e01cc4f'
down_revision: Union[str, Sequence[str], None] = '4d5512e21ca0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add display_order column to sales_persons table
    op.add_column('sales_persons', sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'))
    
    # Add display_order column to contractors table
    op.add_column('contractors', sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove display_order column from contractors table
    op.drop_column('contractors', 'display_order')
    
    # Remove display_order column from sales_persons table
    op.drop_column('sales_persons', 'display_order')
