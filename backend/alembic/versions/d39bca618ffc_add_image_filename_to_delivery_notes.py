"""add_image_filename_to_delivery_notes

Revision ID: d39bca618ffc
Revises: e719581c8f23
Create Date: 2026-02-01 23:33:55.367527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd39bca618ffc'
down_revision: Union[str, Sequence[str], None] = 'e719581c8f23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('delivery_notes', sa.Column('image_filename', sa.String(500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('delivery_notes', 'image_filename')
