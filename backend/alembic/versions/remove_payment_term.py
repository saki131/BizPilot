"""remove payment_term from contractor_invoices

Revision ID: remove_payment_term
Revises: add_tax_rate_sales_inv
Create Date: 2026-02-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_payment_term'
down_revision = 'add_tax_rate_sales_inv'
branch_labels = None
depends_on = None


def upgrade():
    # Remove payment_term column from contractor_invoices
    op.drop_column('contractor_invoices', 'payment_term')


def downgrade():
    # Add payment_term column back if needed to rollback
    op.add_column('contractor_invoices', sa.Column('payment_term', sa.String(length=200), nullable=True))
