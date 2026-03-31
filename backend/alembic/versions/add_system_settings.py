"""add_system_settings

Revision ID: add_system_settings
Revises: update_customer_orders_deposits
Create Date: 2026-04-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_system_settings'
down_revision: Union[str, Sequence[str], None] = 'update_customer_orders_deposits'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'system_settings',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    # デフォルト値を挿入
    op.execute(
        "INSERT INTO system_settings (key, value) VALUES "
        "('gemini_model', 'gemini-3.1-flash-lite-preview'), "
        "('gemini_fallback_model', 'gemini-2.5-flash')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('system_settings')
