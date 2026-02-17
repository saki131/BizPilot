"""remove start_date and end_date from sales_invoices

Revision ID: remove_start_end_dates
Revises: remove_payment_term
Create Date: 2026-02-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_start_end_dates'
down_revision = 'remove_payment_term'
branch_labels = None
depends_on = None


def upgrade():
    # Remove start_date and end_date columns from sales_invoices
    op.drop_column('sales_invoices', 'start_date')
    op.drop_column('sales_invoices', 'end_date')
    
    # Make invoice_date NOT NULL since it's now the primary date field
    op.alter_column('sales_invoices', 'invoice_date',
                    existing_type=sa.Date(),
                    nullable=False)


def downgrade():
    # Add back start_date and end_date columns if needed to rollback
    op.add_column('sales_invoices', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('sales_invoices', sa.Column('end_date', sa.Date(), nullable=True))
    
    # Revert invoice_date to nullable
    op.alter_column('sales_invoices', 'invoice_date',
                    existing_type=sa.Date(),
                    nullable=True)
