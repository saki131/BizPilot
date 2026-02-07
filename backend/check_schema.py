import os
import psycopg2

db_url = "postgresql://neondb_owner:npg_I7YCoVX5ajmL@ep-young-fog-a1v5j4i7-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Check delivery_notes.id column type
cur.execute("""
    SELECT column_name, data_type, udt_name 
    FROM information_schema.columns 
    WHERE table_name='delivery_notes' AND column_name='id'
""")
result = cur.fetchall()
print("delivery_notes.id column info:")
for row in result:
    print(f"  Column: {row[0]}, Type: {row[1]}, UDT: {row[2]}")

# Check alembic version
cur.execute("SELECT version_num FROM alembic_version")
version = cur.fetchone()
print(f"\nCurrent Alembic version: {version[0] if version else 'None'}")

conn.close()
