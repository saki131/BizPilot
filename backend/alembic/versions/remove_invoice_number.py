"""remove invoice_number from sales_invoices

Revision ID: remove_invoice_number
Revises: remove_delivery_note_number
Create Date: 2026-02-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_invoice_number'
down_revision = 'remove_delivery_note_number'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # sales_invoicesテーブルからinvoice_numberカラムを削除
    op.drop_column('sales_invoices', 'invoice_number')


def downgrade() -> None:
    # ロールバック: invoice_numberカラムを追加
    op.add_column('sales_invoices', sa.Column('invoice_number', sa.String(length=50), nullable=True))
    # デフォルト値を設定してからnot nullに変更
    op.execute("UPDATE sales_invoices SET invoice_number = '[COMPANY_REGISTRATION_NUMBER]' WHERE invoice_number IS NULL")
    op.alter_column('sales_invoices', 'invoice_number', nullable=False)
