"""add foreign key indexes for performance

Revision ID: add_fk_indexes
Revises: f17dfaf1280e
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_fk_indexes'
down_revision = 'f17dfaf1280e'
branch_labels = None
depends_on = None


def upgrade():
    # Add indexes on foreign keys for better JOIN performance
    
    # delivery_notes table
    op.create_index('ix_delivery_notes_sales_person_id', 'delivery_notes', ['sales_person_id'])
    op.create_index('ix_delivery_notes_tax_rate_id', 'delivery_notes', ['tax_rate_id'])
    op.create_index('ix_delivery_notes_billing_date', 'delivery_notes', ['billing_date'])
    op.create_index('ix_delivery_notes_deleted_flag', 'delivery_notes', ['deleted_flag'])
    
    # delivery_note_details table
    op.create_index('ix_delivery_note_details_delivery_note_id', 'delivery_note_details', ['delivery_note_id'])
    op.create_index('ix_delivery_note_details_product_id', 'delivery_note_details', ['product_id'])
    
    # sales_invoices table
    op.create_index('ix_sales_invoices_sales_person_id', 'sales_invoices', ['sales_person_id'])
    op.create_index('ix_sales_invoices_discount_rate_id', 'sales_invoices', ['discount_rate_id'])
    op.create_index('ix_sales_invoices_deleted_flag', 'sales_invoices', ['deleted_flag'])
    op.create_index('ix_sales_invoices_created_at', 'sales_invoices', ['created_at'])
    
    # sales_invoice_details table
    op.create_index('ix_sales_invoice_details_sales_invoice_id', 'sales_invoice_details', ['sales_invoice_id'])
    op.create_index('ix_sales_invoice_details_product_id', 'sales_invoice_details', ['product_id'])
    
    # contractor_invoices table
    op.create_index('ix_contractor_invoices_contractor_id', 'contractor_invoices', ['contractor_id'])
    op.create_index('ix_contractor_invoices_discount_rate_id', 'contractor_invoices', ['discount_rate_id'])
    op.create_index('ix_contractor_invoices_tax_rate_id', 'contractor_invoices', ['tax_rate_id'])
    op.create_index('ix_contractor_invoices_deleted_flag', 'contractor_invoices', ['deleted_flag'])
    op.create_index('ix_contractor_invoices_invoice_date', 'contractor_invoices', ['invoice_date'])
    
    # contractor_invoice_details table
    op.create_index('ix_contractor_invoice_details_contractor_invoice_id', 'contractor_invoice_details', ['contractor_invoice_id'])
    op.create_index('ix_contractor_invoice_details_product_id', 'contractor_invoice_details', ['product_id'])


def downgrade():
    # Remove indexes
    
    # delivery_notes table
    op.drop_index('ix_delivery_notes_sales_person_id', 'delivery_notes')
    op.drop_index('ix_delivery_notes_tax_rate_id', 'delivery_notes')
    op.drop_index('ix_delivery_notes_billing_date', 'delivery_notes')
    op.drop_index('ix_delivery_notes_deleted_flag', 'delivery_notes')
    
    # delivery_note_details table
    op.drop_index('ix_delivery_note_details_delivery_note_id', 'delivery_note_details')
    op.drop_index('ix_delivery_note_details_product_id', 'delivery_note_details')
    
    # sales_invoices table
    op.drop_index('ix_sales_invoices_sales_person_id', 'sales_invoices')
    op.drop_index('ix_sales_invoices_discount_rate_id', 'sales_invoices')
    op.drop_index('ix_sales_invoices_deleted_flag', 'sales_invoices')
    op.drop_index('ix_sales_invoices_created_at', 'sales_invoices')
    
    # sales_invoice_details table
    op.drop_index('ix_sales_invoice_details_sales_invoice_id', 'sales_invoice_details')
    op.drop_index('ix_sales_invoice_details_product_id', 'sales_invoice_details')
    
    # contractor_invoices table
    op.drop_index('ix_contractor_invoices_contractor_id', 'contractor_invoices')
    op.drop_index('ix_contractor_invoices_discount_rate_id', 'contractor_invoices')
    op.drop_index('ix_contractor_invoices_tax_rate_id', 'contractor_invoices')
    op.drop_index('ix_contractor_invoices_deleted_flag', 'contractor_invoices')
    op.drop_index('ix_contractor_invoices_invoice_date', 'contractor_invoices')
    
    # contractor_invoice_details table
    op.drop_index('ix_contractor_invoice_details_contractor_invoice_id', 'contractor_invoice_details')
    op.drop_index('ix_contractor_invoice_details_product_id', 'contractor_invoice_details')
