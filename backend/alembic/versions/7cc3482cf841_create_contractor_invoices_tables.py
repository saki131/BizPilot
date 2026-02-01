"""create contractor invoices tables

Revision ID: 7cc3482cf841
Revises: d39bca618ffc
Create Date: 2026-02-02 00:54:58.807122

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7cc3482cf841'
down_revision: Union[str, Sequence[str], None] = 'd39bca618ffc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create contractor_invoices table
    op.create_table(
        'contractor_invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contractor_id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('discount_rate_id', sa.Integer(), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=True),
        sa.Column('receipt_date', sa.Date(), nullable=True),
        sa.Column('non_discountable_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('note', sa.String(500), nullable=True),
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
        sa.ForeignKeyConstraint(['contractor_id'], ['contractors.id'], ),
        sa.ForeignKeyConstraint(['discount_rate_id'], ['discount_rates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contractor_invoices_id'), 'contractor_invoices', ['id'], unique=False)
    
    # Create contractor_invoice_details table
    op.create_table(
        'contractor_invoice_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contractor_invoice_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('total_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unit_price', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['contractor_invoice_id'], ['contractor_invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contractor_invoice_details_id'), 'contractor_invoice_details', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_contractor_invoice_details_id'), table_name='contractor_invoice_details')
    op.drop_table('contractor_invoice_details')
    op.drop_index(op.f('ix_contractor_invoices_id'), table_name='contractor_invoices')
    op.drop_table('contractor_invoices')
