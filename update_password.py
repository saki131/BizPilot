import sys
sys.path.append('backend')

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User, Base

# Create a session
db = SessionLocal()

# Update user password
user = db.query(User).filter(User.username == "admin").first()
if user:
    user.hashed_password = "$pbkdf2-sha256$29000$lVIKYWxtLaXU2ltr7b2X8g$5ATahvjeCcApmyuAUPt/ORwwThnzvsRuPEuKyLbPBZ8"
    db.commit()
    print(f"User password updated: {user.username}")
else:
    print("User not found")

db.close()