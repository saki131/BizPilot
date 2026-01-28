"""add_threshold_amount_to_discount_rates_and_create_invoice_tables

Revision ID: 087a55338e39
Revises: 
Create Date: 2026-01-25 23:22:00.913092

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '087a55338e39'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # discount_ratesにthreshold_amountカラムを追加
    op.add_column('discount_rates', sa.Column('threshold_amount', sa.Integer(), nullable=True, server_default='0'))
    
    # sales_invoicesテーブルを削除して再作成（既存のテーブルをアップグレード）
    op.drop_table('sales_invoices')
    
    # sales_invoicesテーブル作成
    op.create_table('sales_invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sales_person_id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('discount_rate_id', sa.Integer(), nullable=False),
        sa.Column('quota_subtotal', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quota_discount_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quota_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('non_quota_subtotal', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('non_quota_discount_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('non_quota_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_amount_ex_tax', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tax_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_amount_inc_tax', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['discount_rate_id'], ['discount_rates.id'], ),
        sa.ForeignKeyConstraint(['sales_person_id'], ['sales_persons.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_invoices_id'), 'sales_invoices', ['id'], unique=False)
    
    # sales_invoice_detailsテーブル作成
    op.create_table('sales_invoice_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sales_invoice_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('total_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unit_price', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['sales_invoice_id'], ['sales_invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_invoice_details_id'), 'sales_invoice_details', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_sales_invoice_details_id'), table_name='sales_invoice_details')
    op.drop_table('sales_invoice_details')
    op.drop_index(op.f('ix_sales_invoices_id'), table_name='sales_invoices')
    op.drop_table('sales_invoices')
    op.drop_column('discount_rates', 'threshold_amount')
