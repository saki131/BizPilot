"""add_customers_orders_deposits

Revision ID: 05575674725b
Revises: remove_start_end_dates
Create Date: 2026-03-08 19:04:35.001766

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05575674725b'
down_revision: Union[str, Sequence[str], None] = 'remove_start_end_dates'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. customers テーブル作成（customer_orders の外部キー先）
    op.create_table('customers',
        sa.Column('customer_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('name_kana', sa.String(length=200), nullable=True),
        sa.Column('deleted_flag', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('customer_id')
    )
    op.create_index(op.f('ix_customers_customer_id'), 'customers', ['customer_id'], unique=False)

    # 2. deposit_records テーブル作成（customer_orders の外部キー先、matched_order_id は後で追加）
    op.create_table('deposit_records',
        sa.Column('deposit_record_id', sa.UUID(), nullable=False),
        sa.Column('deposit_date', sa.Date(), nullable=False),
        sa.Column('depositor_name', sa.String(length=200), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('detail1', sa.String(length=500), nullable=True),
        sa.Column('detail2', sa.String(length=500), nullable=True),
        sa.Column('matched_order_id', sa.UUID(), nullable=True),
        sa.Column('upload_batch_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('deposit_record_id')
    )
    op.create_index(op.f('ix_deposit_records_deposit_record_id'), 'deposit_records', ['deposit_record_id'], unique=False)

    # 3. customer_orders テーブル作成
    op.create_table('customer_orders',
        sa.Column('customer_order_id', sa.UUID(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('order_date', sa.Date(), nullable=False),
        sa.Column('order_amount', sa.Integer(), nullable=False),
        sa.Column('payment_due_date', sa.Date(), nullable=False),
        sa.Column('payment_status', sa.String(length=20), nullable=False, server_default=sa.text("'unpaid'")),
        sa.Column('deposit_record_id', sa.UUID(), nullable=True),
        sa.Column('memo', sa.Text(), nullable=True),
        sa.Column('deleted_flag', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], ),
        sa.ForeignKeyConstraint(['deposit_record_id'], ['deposit_records.deposit_record_id'], ),
        sa.PrimaryKeyConstraint('customer_order_id')
    )
    op.create_index(op.f('ix_customer_orders_customer_order_id'), 'customer_orders', ['customer_order_id'], unique=False)
    op.create_index('idx_customer_orders_customer', 'customer_orders', ['customer_id'], unique=False)
    op.create_index('idx_customer_orders_status', 'customer_orders', ['payment_status'], unique=False)
    op.create_index('idx_customer_orders_due_date', 'customer_orders', ['payment_due_date'], unique=False)

    # 4. deposit_records に matched_order_id の外部キー制約を追加
    op.create_foreign_key(
        'fk_deposit_records_matched_order',
        'deposit_records', 'customer_orders',
        ['matched_order_id'], ['customer_order_id']
    )
    op.create_index('idx_deposit_records_matched', 'deposit_records', ['matched_order_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_deposit_records_matched_order', 'deposit_records', type_='foreignkey')
    op.drop_index('idx_deposit_records_matched', table_name='deposit_records')
    op.drop_index('idx_customer_orders_due_date', table_name='customer_orders')
    op.drop_index('idx_customer_orders_status', table_name='customer_orders')
    op.drop_index('idx_customer_orders_customer', table_name='customer_orders')
    op.drop_index(op.f('ix_customer_orders_customer_order_id'), table_name='customer_orders')
    op.drop_table('customer_orders')
    op.drop_index(op.f('ix_deposit_records_deposit_record_id'), table_name='deposit_records')
    op.drop_table('deposit_records')
    op.drop_index(op.f('ix_customers_customer_id'), table_name='customers')
    op.drop_table('customers')
