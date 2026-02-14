"""Initialize database schema and master data."""
print("=== START init_db.py ===", flush=True)

import sys
import os

print(f"Python version: {sys.version}", flush=True)
print(f"Current directory: {os.getcwd()}", flush=True)
print(f"DATABASE_URL exists: {'DATABASE_URL' in os.environ}", flush=True)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("Importing database module...", flush=True)
    from database import engine
    from sqlalchemy import text, inspect
    import subprocess
    import traceback
    
    # Check if tables already exist
    print("Checking if tables already exist...", flush=True)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"Existing tables: {existing_tables}", flush=True)
    
    if 'users' in existing_tables and 'discount_rates' in existing_tables:
        print("✓ Tables already exist. Skipping table creation.", flush=True)
    else:
        print("Importing models...", flush=True)
        from models import Base
        print("✓ Models imported successfully!", flush=True)
        
        print("Creating all tables...", flush=True)
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully!", flush=True)
        
        # Stamp alembic version to latest
        print("Marking database as up-to-date with migrations...", flush=True)
        import subprocess
        result = subprocess.run(["alembic", "stamp", "head"], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode != 0:
            print(f"Warning: Failed to stamp alembic version: {result.stderr}", flush=True)
        else:
            print("✓ Database marked as up-to-date", flush=True)
except Exception as e:
    print(f"ERROR: Failed to create tables: {e}", flush=True)
    print(traceback.format_exc(), flush=True)
    sys.exit(1)

# Check if master data already exists
try:
    print("Checking if master data exists...", flush=True)
    with engine.connect() as conn:
        from sqlalchemy import text
        # Check if discount_rates table has data
        if 'discount_rates' in existing_tables:
            result = conn.execute(text("SELECT COUNT(*) FROM discount_rates"))
            count = result.scalar()
            if count > 0:
                print(f"✓ Master data already exists ({count} discount rates). Skipping initialization.", flush=True)
                print("✓ Database initialization complete!", flush=True)
                sys.exit(0)
except Exception as e:
    print(f"Warning: Could not check master data: {e}", flush=True)

try:
    print("Initializing master data...", flush=True)
    result = subprocess.run([sys.executable, "init_master_data.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error initializing master data:", flush=True)
        print(f"STDOUT: {result.stdout}", flush=True)
        print(f"STDERR: {result.stderr}", flush=True)
        sys.exit(1)
    print(result.stdout, flush=True)
    print("✓ Database initialization complete!", flush=True)
except Exception as e:
    print(f"ERROR: Failed to initialize master data: {e}", flush=True)
    print(traceback.format_exc(), flush=True)
    sys.exit(1)

