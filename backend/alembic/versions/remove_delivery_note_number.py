"""remove delivery_note_number column

Revision ID: remove_delivery_note_number
Revises: 
Create Date: 2026-02-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_delivery_note_number'
down_revision = 'eb97b1d1876e'  # add_foreign_key_indexes
branch_labels = None
depends_on = None


def upgrade() -> None:
    # delivery_notesテーブルからdelivery_note_numberカラムを削除
    op.drop_constraint('delivery_notes_delivery_note_number_key', 'delivery_notes', type_='unique')
    op.drop_column('delivery_notes', 'delivery_note_number')


def downgrade() -> None:
    # ロールバック: delivery_note_numberカラムを追加
    op.add_column('delivery_notes', sa.Column('delivery_note_number', sa.String(length=50), nullable=True))
    # まずnullableで追加し、既存レコードにデフォルト値を設定してからnot nullに変更
    op.execute("UPDATE delivery_notes SET delivery_note_number = 'DN-' || substring(delivery_note_id::text, 1, 8) WHERE delivery_note_number IS NULL")
    op.alter_column('delivery_notes', 'delivery_note_number', nullable=False)
    op.create_unique_constraint('delivery_notes_delivery_note_number_key', 'delivery_notes', ['delivery_note_number'])
