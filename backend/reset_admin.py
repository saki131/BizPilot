import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from models import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def reset_admin_password():
    db = SessionLocal()
    try:
        # Find admin user
        user = db.query(User).filter(User.username == "admin").first()
        
        if not user:
            print("❌ Admin user not found")
            return
        
        # Update password with proper bcrypt hash
        new_password = "password123"
        hashed_password = pwd_context.hash(new_password)
        user.hashed_password = hashed_password
        
        db.commit()
        print(f"✓ Admin password reset successfully!")
        print(f"  Username: admin")
        print(f"  Password: password123")
        print(f"  Hash: {hashed_password[:60]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()
