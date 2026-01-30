"""Create a new admin user."""
import sys
from passlib.context import CryptContext
from database import SessionLocal
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(username: str, password: str):
    """Create a new user with hashed password."""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return False
        
        # Hash password
        hashed_password = pwd_context.hash(password)
        
        # Create new user
        new_user = User(
            username=username,
            hashed_password=hashed_password
        )
        db.add(new_user)
        db.commit()
        print(f"✓ User '{username}' created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_user.py <username> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    success = create_user(username, password)
    sys.exit(0 if success else 1)
