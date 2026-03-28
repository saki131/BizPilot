"""update customer_orders and deposit_records for new requirements

Revision ID: update_customer_orders_deposits
Revises: 05575674725b
Create Date: 2026-03-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'update_customer_orders_deposits'
down_revision: Union[str, Sequence[str], None] = '05575674725b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # deposit_records に transaction_id と balance カラムを追加
    op.add_column('deposit_records',
        sa.Column('transaction_id', sa.String(length=100), nullable=True))
    op.add_column('deposit_records',
        sa.Column('balance', sa.Integer(), nullable=True))

    # overdue ステータスを unpaid に戻す
    op.execute("UPDATE customer_orders SET payment_status = 'unpaid' WHERE payment_status = 'overdue'")


def downgrade() -> None:
    op.drop_column('deposit_records', 'balance')
    op.drop_column('deposit_records', 'transaction_id')
