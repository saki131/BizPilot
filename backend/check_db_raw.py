import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, username, hashed_password, created_at FROM users"))
    rows = result.fetchall()
    
    print(f"\n=== Total users: {len(rows)} ===\n")
    
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Username: {row[1]}")
        print(f"Hash: {row[2]}")
        print(f"Hash length: {len(row[2]) if row[2] else 0}")
        print(f"Hash starts with: {row[2][:10] if row[2] else 'None'}")
        print(f"Created: {row[3]}")
        print("-" * 80)
