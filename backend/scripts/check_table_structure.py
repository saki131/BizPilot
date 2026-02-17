"""
staging環境のsales_invoicesテーブルの構造を確認
"""
import psycopg2
import os
import sys

database_url = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(database_url, connect_timeout=30)
cursor = conn.cursor()

# テーブル名を引数から取得、デフォルトはdelivery_notes
table_name = sys.argv[1] if len(sys.argv) > 1 else 'delivery_notes'

# カラム一覧を取得
cursor.execute("""
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name = %s
    ORDER BY ordinal_position
""", (table_name,))

print(f"{table_name}テーブルのカラム構成:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"{row[0]:<30} {row[1]:<20} {'NULL' if row[2] == 'YES' else 'NOT NULL'}")

cursor.close()
conn.close()
