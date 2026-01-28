import sys
sys.path.append('backend')

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User, Base

# Create tables if not exist
Base.metadata.create_all(bind=engine)

# Create a session
db = SessionLocal()

# Create user
user = User(username="admin", hashed_password="$2b$12$fqx29zKraSIwtLPSwb817.wuGSDKAleBD0otgqFRulNqVCh/VzniW")
db.add(user)
db.commit()
db.refresh(user)

print(f"User created: {user.username}")

db.close()