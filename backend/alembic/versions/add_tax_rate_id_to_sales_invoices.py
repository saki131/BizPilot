"""add tax_rate_id to sales_invoices

Revision ID: add_tax_rate_id_to_sales_invoices
Revises: remove_invoice_number
Create Date: 2026-02-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_tax_rate_sales_inv'
down_revision = 'remove_invoice_number'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # sales_invoicesテーブルにtax_rate_idカラムを追加
    # まずNULL可能で追加
    op.add_column('sales_invoices', sa.Column('tax_rate_id', sa.Integer(), nullable=True))
    
    # デフォルト値を設定（tax_rate_id=1）
    op.execute("UPDATE sales_invoices SET tax_rate_id = 1 WHERE tax_rate_id IS NULL")
    
    # NOT NULL制約を追加
    op.alter_column('sales_invoices', 'tax_rate_id', nullable=False)
    
    # 外部キー制約を追加
    op.create_foreign_key(
        'fk_sales_invoices_tax_rate_id',
        'sales_invoices', 'tax_rates',
        ['tax_rate_id'], ['tax_rate_id']
    )


def downgrade() -> None:
    # 外部キー制約を削除
    op.drop_constraint('fk_sales_invoices_tax_rate_id', 'sales_invoices', type_='foreignkey')
    
    # tax_rate_idカラムを削除
    op.drop_column('sales_invoices', 'tax_rate_id')
