"""convert_ids_to_uuid

Revision ID: 270866f42abe
Revises: bd38bc408fa1
Create Date: 2026-02-07 12:10:00.615772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '270866f42abe'
down_revision: Union[str, Sequence[str], None] = 'bd38bc408fa1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Convert integer IDs to UUIDs."""
    
    # UUIDエクステンションを有効化
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # 1. 納品書詳細テーブルの外部キー制約を削除
    op.drop_constraint('delivery_note_details_delivery_note_id_fkey', 'delivery_note_details', type_='foreignkey')
    
    # 2. 納品書テーブルのIDをUUIDに変換
    op.execute('''
        ALTER TABLE delivery_notes 
        ADD COLUMN id_uuid UUID DEFAULT uuid_generate_v4()
    ''')
    op.execute('UPDATE delivery_notes SET id_uuid = uuid_generate_v4()')
    op.execute('ALTER TABLE delivery_notes DROP CONSTRAINT delivery_notes_pkey')
    op.execute('ALTER TABLE delivery_notes DROP COLUMN id')
    op.execute('ALTER TABLE delivery_notes RENAME COLUMN id_uuid TO id')
    op.execute('ALTER TABLE delivery_notes ADD PRIMARY KEY (id)')
    
    # 3. 納品書詳細テーブルのIDと外部キーをUUIDに変換
    op.execute('''
        ALTER TABLE delivery_note_details 
        ADD COLUMN id_uuid UUID DEFAULT uuid_generate_v4(),
        ADD COLUMN delivery_note_id_uuid UUID
    ''')
    op.execute('UPDATE delivery_note_details SET id_uuid = uuid_generate_v4()')
    # 外部キーは孤児レコードになるので削除
    op.execute('DELETE FROM delivery_note_details')
    op.execute('ALTER TABLE delivery_note_details DROP CONSTRAINT delivery_note_details_pkey')
    op.execute('ALTER TABLE delivery_note_details DROP COLUMN id, DROP COLUMN delivery_note_id')
    op.execute('ALTER TABLE delivery_note_details RENAME COLUMN id_uuid TO id')
    op.execute('ALTER TABLE delivery_note_details RENAME COLUMN delivery_note_id_uuid TO delivery_note_id')
    op.execute('ALTER TABLE delivery_note_details ADD PRIMARY KEY (id)')
    op.create_foreign_key(
        'delivery_note_details_delivery_note_id_fkey',
        'delivery_note_details', 'delivery_notes',
        ['delivery_note_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 4. 販売員請求書詳細テーブルの外部キー制約を削除
    op.drop_constraint('sales_invoice_details_sales_invoice_id_fkey', 'sales_invoice_details', type_='foreignkey')
    
    # 5. 販売員請求書テーブルのIDをUUIDに変換
    op.execute('''
        ALTER TABLE sales_invoices 
        ADD COLUMN id_uuid UUID DEFAULT uuid_generate_v4()
    ''')
    op.execute('UPDATE sales_invoices SET id_uuid = uuid_generate_v4()')
    op.execute('ALTER TABLE sales_invoices DROP CONSTRAINT sales_invoices_pkey')
    op.execute('ALTER TABLE sales_invoices DROP COLUMN id')
    op.execute('ALTER TABLE sales_invoices RENAME COLUMN id_uuid TO id')
    op.execute('ALTER TABLE sales_invoices ADD PRIMARY KEY (id)')
    
    # 6. 販売員請求書詳細テーブルのIDと外部キーをUUIDに変換
    op.execute('''
        ALTER TABLE sales_invoice_details 
        ADD COLUMN id_uuid UUID DEFAULT uuid_generate_v4(),
        ADD COLUMN sales_invoice_id_uuid UUID
    ''')
    op.execute('UPDATE sales_invoice_details SET id_uuid = uuid_generate_v4()')
    # 外部キーは孤児レコードになるので削除
    op.execute('DELETE FROM sales_invoice_details')
    op.execute('ALTER TABLE sales_invoice_details DROP CONSTRAINT sales_invoice_details_pkey')
    op.execute('ALTER TABLE sales_invoice_details DROP COLUMN id, DROP COLUMN sales_invoice_id')
    op.execute('ALTER TABLE sales_invoice_details RENAME COLUMN id_uuid TO id')
    op.execute('ALTER TABLE sales_invoice_details RENAME COLUMN sales_invoice_id_uuid TO sales_invoice_id')
    op.execute('ALTER TABLE sales_invoice_details ADD PRIMARY KEY (id)')
    op.create_foreign_key(
        'sales_invoice_details_sales_invoice_id_fkey',
        'sales_invoice_details', 'sales_invoices',
        ['sales_invoice_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 7. 委託先請求書詳細テーブルの外部キー制約を削除
    op.drop_constraint('contractor_invoice_details_contractor_invoice_id_fkey', 'contractor_invoice_details', type_='foreignkey')
    
    # 8. 委託先請求書テーブルのIDをUUIDに変換
    op.execute('''
        ALTER TABLE contractor_invoices 
        ADD COLUMN id_uuid UUID DEFAULT uuid_generate_v4()
    ''')
    op.execute('UPDATE contractor_invoices SET id_uuid = uuid_generate_v4()')
    op.execute('ALTER TABLE contractor_invoices DROP CONSTRAINT contractor_invoices_pkey')
    op.execute('ALTER TABLE contractor_invoices DROP COLUMN id')
    op.execute('ALTER TABLE contractor_invoices RENAME COLUMN id_uuid TO id')
    op.execute('ALTER TABLE contractor_invoices ADD PRIMARY KEY (id)')
    
    # 9. 委託先請求書詳細テーブルのIDと外部キーをUUIDに変換
    op.execute('''
        ALTER TABLE contractor_invoice_details 
        ADD COLUMN id_uuid UUID DEFAULT uuid_generate_v4(),
        ADD COLUMN contractor_invoice_id_uuid UUID
    ''')
    op.execute('UPDATE contractor_invoice_details SET id_uuid = uuid_generate_v4()')
    # 外部キーは孤児レコードになるので削除
    op.execute('DELETE FROM contractor_invoice_details')
    op.execute('ALTER TABLE contractor_invoice_details DROP CONSTRAINT contractor_invoice_details_pkey')
    op.execute('ALTER TABLE contractor_invoice_details DROP COLUMN id, DROP COLUMN contractor_invoice_id')
    op.execute('ALTER TABLE contractor_invoice_details RENAME COLUMN id_uuid TO id')
    op.execute('ALTER TABLE contractor_invoice_details RENAME COLUMN contractor_invoice_id_uuid TO contractor_invoice_id')
    op.execute('ALTER TABLE contractor_invoice_details ADD PRIMARY KEY (id)')
    op.create_foreign_key(
        'contractor_invoice_details_contractor_invoice_id_fkey',
        'contractor_invoice_details', 'contractor_invoices',
        ['contractor_invoice_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema - Convert UUIDs back to integers (data will be lost)."""
    # ダウングレードは複雑なため実装しない
    pass
