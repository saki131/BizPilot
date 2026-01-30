import os
import sys
import bcrypt
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Delete all users
    conn.execute(text("DELETE FROM users"))
    conn.commit()
    print("✓ Deleted all users")
    
    # Create new admin user with direct bcrypt
    password = "password123"
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn.execute(
        text("INSERT INTO users (username, hashed_password) VALUES (:username, :password)"),
        {"username": "admin", "password": hashed}
    )
    conn.commit()
    print(f"✓ Created admin user")
    print(f"  Username: admin")
    print(f"  Password: password123")
    print(f"  Hash: {hashed}")
    print(f"  Hash length: {len(hashed)}")
    
    # Verify
    result = conn.execute(text("SELECT username, hashed_password FROM users WHERE username = 'admin'"))
    row = result.fetchone()
    print(f"\n✓ Verification:")
    print(f"  DB Username: {row[0]}")
    print(f"  DB Hash: {row[1]}")
    
    # Test password verification with direct bcrypt
    verify_result = bcrypt.checkpw(password.encode('utf-8'), row[1].encode('utf-8'))
    print(f"  Password verification: {'✓ SUCCESS' if verify_result else '❌ FAILED'}")
