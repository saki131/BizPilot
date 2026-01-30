"""Initialize database schema directly."""
from models import Base
from database import engine

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("✓ All tables created successfully!")
