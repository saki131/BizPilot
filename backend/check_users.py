import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from models import User

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def check_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        print(f"\n=== Total users: {len(users)} ===\n")
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Hash: {user.hashed_password[:60]}...")
            print(f"Hash type: {user.hashed_password[:4] if user.hashed_password else 'None'}")
            print(f"Hash length: {len(user.hashed_password) if user.hashed_password else 0}")
            print(f"Created: {user.created_at}")
            print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
