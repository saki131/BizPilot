"""add_receipt_date_to_contractor_invoices

Revision ID: 3857dc264a04
Revises: 270866f42abe
Create Date: 2026-02-08 18:46:32.777303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3857dc264a04'
down_revision: Union[str, Sequence[str], None] = '270866f42abe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('contractor_invoices', sa.Column('receipt_date', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('contractor_invoices', 'receipt_date')
