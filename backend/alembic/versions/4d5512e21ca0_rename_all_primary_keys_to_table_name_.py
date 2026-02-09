"""Rename all primary keys to table_name_id format

Revision ID: 4d5512e21ca0
Revises: 2f94c130cdf8
Create Date: 2026-02-08 23:14:27.926661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4d5512e21ca0'
down_revision: Union[str, Sequence[str], None] = '2f94c130cdf8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - DROP all tables and recreate with new primary key names."""
    
    # Drop all tables in correct order (dependencies first)
    op.drop_table('contractor_invoice_details')
    op.drop_table('contractor_invoices')
    op.drop_table('sales_invoice_details')
    op.drop_table('sales_invoices')
    op.drop_table('delivery_note_details')
    op.drop_table('delivery_notes')
    op.drop_table('discount_rates')
    op.drop_table('tax_rates')
    op.drop_table('products')
    op.drop_table('contractors')
    op.drop_table('sales_persons')
    op.drop_table('users')
    
    # Recreate tables with new primary key names
    
    # Users table
    op.create_table('users',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('deleted_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_user_id'), 'users', ['user_id'], unique=False)
    
    # SalesPerson table
    op.create_table('sales_persons',
        sa.Column('sales_person_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('deleted_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('sales_person_id')
    )
    op.create_index(op.f('ix_sales_persons_sales_person_id'), 'sales_persons', ['sales_person_id'], unique=False)
    
    # Product table
    op.create_table('products',
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('discount_exclusion_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('quota_exclusion_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('quota_target_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('deleted_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('display_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('product_id')
    )
    op.create_index(op.f('ix_products_product_id'), 'products', ['product_id'], unique=False)
    
    # Contractor table
    op.create_table('contractors',
        sa.Column('contractor_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('deleted_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('contractor_id')
    )
    op.create_index(op.f('ix_contractors_contractor_id'), 'contractors', ['contractor_id'], unique=False)
    
    # TaxRate table
    op.create_table('tax_rates',
        sa.Column('tax_rate_id', sa.Integer(), nullable=False),
        sa.Column('rate', sa.DECIMAL(precision=4, scale=2), nullable=False),
        sa.Column('display_name', sa.String(length=20), nullable=False),
        sa.Column('deleted_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('tax_rate_id')
    )
    op.create_index(op.f('ix_tax_rates_tax_rate_id'), 'tax_rates', ['tax_rate_id'], unique=False)
    
    # DiscountRate table
    op.create_table('discount_rates',
        sa.Column('discount_rate_id', sa.Integer(), nullable=False),
        sa.Column('rate', sa.DECIMAL(precision=4, scale=2), nullable=False),
        sa.Column('threshold_amount', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('sales_person_flag', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('deleted_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('discount_rate_id')
    )
    op.create_index(op.f('ix_discount_rates_discount_rate_id'), 'discount_rates', ['discount_rate_id'], unique=False)
    
    # DeliveryNote table
    op.create_table('delivery_notes',
        sa.Column('delivery_note_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sales_person_id', sa.Integer(), nullable=True),
        sa.Column('tax_rate_id', sa.Integer(), nullable=True),
        sa.Column('quota_amount', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('non_quota_amount', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('tax_amount', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_amount_ex_tax', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_amount_inc_tax', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('delivery_note_number', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('delivery_date', sa.TIMESTAMP(), nullable=False),
        sa.Column('billing_date', sa.TIMESTAMP(), nullable=False),
        sa.Column('image_recognition_data', sa.JSON(), nullable=True),
        sa.Column('image_filename', sa.String(length=500), nullable=True),
        sa.Column('deleted_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['sales_person_id'], ['sales_persons.sales_person_id'], ),
        sa.ForeignKeyConstraint(['tax_rate_id'], ['tax_rates.tax_rate_id'], ),
        sa.PrimaryKeyConstraint('delivery_note_id'),
        sa.UniqueConstraint('delivery_note_number')
    )
    op.create_index(op.f('ix_delivery_notes_delivery_note_id'), 'delivery_notes', ['delivery_note_id'], unique=False)
    
    # DeliveryNoteDetail table
    op.create_table('delivery_note_details',
        sa.Column('delivery_note_detail_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('delivery_note_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('remarks', sa.String(length=200), nullable=True),
        sa.Column('deleted_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['delivery_note_id'], ['delivery_notes.delivery_note_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], ),
        sa.PrimaryKeyConstraint('delivery_note_detail_id')
    )
    op.create_index(op.f('ix_delivery_note_details_delivery_note_detail_id'), 'delivery_note_details', ['delivery_note_detail_id'], unique=False)
    
    # SalesInvoice table
    op.create_table('sales_invoices',
        sa.Column('sales_invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sales_person_id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('discount_rate_id', sa.Integer(), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=True),
        sa.Column('receipt_date', sa.Date(), nullable=True),
        sa.Column('non_discountable_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('note', sa.String(length=500), nullable=True),
        sa.Column('quota_subtotal', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quota_discount_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quota_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('non_quota_subtotal', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('non_quota_discount_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('non_quota_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_amount_ex_tax', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tax_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_amount_inc_tax', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deleted_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['discount_rate_id'], ['discount_rates.discount_rate_id'], ),
        sa.ForeignKeyConstraint(['sales_person_id'], ['sales_persons.sales_person_id'], ),
        sa.PrimaryKeyConstraint('sales_invoice_id')
    )
    op.create_index(op.f('ix_sales_invoices_sales_invoice_id'), 'sales_invoices', ['sales_invoice_id'], unique=False)
    
    # SalesInvoiceDetail table
    op.create_table('sales_invoice_details',
        sa.Column('sales_invoice_detail_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sales_invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('total_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unit_price', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('deleted_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], ),
        sa.ForeignKeyConstraint(['sales_invoice_id'], ['sales_invoices.sales_invoice_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('sales_invoice_detail_id')
    )
    op.create_index(op.f('ix_sales_invoice_details_sales_invoice_detail_id'), 'sales_invoice_details', ['sales_invoice_detail_id'], unique=False)
    
    # ContractorInvoice table
    op.create_table('contractor_invoices',
        sa.Column('contractor_invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contractor_id', sa.Integer(), nullable=False),
        sa.Column('discount_rate_id', sa.Integer(), nullable=False),
        sa.Column('tax_rate_id', sa.Integer(), nullable=False),
        sa.Column('non_discountable_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quota_subtotal', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quota_discount_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quota_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('non_quota_subtotal', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('non_quota_discount_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('non_quota_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_amount_ex_tax', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_discount_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_after_discount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tax_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_amount_inc_tax', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('note', sa.String(length=500), nullable=True),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('receipt_date', sa.Date(), nullable=True),
        sa.Column('payment_due_date', sa.Date(), nullable=True),
        sa.Column('payment_term', sa.String(length=200), nullable=True),
        sa.Column('deleted_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['contractor_id'], ['contractors.contractor_id'], ),
        sa.ForeignKeyConstraint(['discount_rate_id'], ['discount_rates.discount_rate_id'], ),
        sa.ForeignKeyConstraint(['tax_rate_id'], ['tax_rates.tax_rate_id'], ),
        sa.PrimaryKeyConstraint('contractor_invoice_id')
    )
    op.create_index(op.f('ix_contractor_invoices_contractor_invoice_id'), 'contractor_invoices', ['contractor_invoice_id'], unique=False)
    
    # ContractorInvoiceDetail table
    op.create_table('contractor_invoice_details',
        sa.Column('contractor_invoice_detail_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contractor_invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('total_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unit_price', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('deleted_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['contractor_invoice_id'], ['contractor_invoices.contractor_invoice_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], ),
        sa.PrimaryKeyConstraint('contractor_invoice_detail_id')
    )
    op.create_index(op.f('ix_contractor_invoice_details_contractor_invoice_detail_id'), 'contractor_invoice_details', ['contractor_invoice_detail_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop all tables
    op.drop_table('contractor_invoice_details')
    op.drop_table('contractor_invoices')
    op.drop_table('sales_invoice_details')
    op.drop_table('sales_invoices')
    op.drop_table('delivery_note_details')
    op.drop_table('delivery_notes')
    op.drop_table('discount_rates')
    op.drop_table('tax_rates')
    op.drop_table('products')
    op.drop_table('contractors')
    op.drop_table('sales_persons')
    op.drop_table('users')

