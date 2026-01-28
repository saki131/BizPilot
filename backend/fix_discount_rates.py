"""Add threshold_amount column to discount_rates table."""
from sqlalchemy import text, inspect
from database import SessionLocal, engine

def check_and_add_threshold_amount():
    # Check current columns
    inspector = inspect(engine)
    columns = inspector.get_columns('discount_rates')
    column_names = [col['name'] for col in columns]
    
    print(f"Current discount_rates columns: {column_names}")
    
    if 'threshold_amount' in column_names:
        print("✅ threshold_amount already exists!")
        return
    
    print("❌ threshold_amount does NOT exist. Adding it now...")
    
    db = SessionLocal()
    try:
        db.execute(text("""
            ALTER TABLE discount_rates 
            ADD COLUMN threshold_amount INTEGER DEFAULT 0 NOT NULL
        """))
        db.commit()
        print("✅ threshold_amount column added successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()
    
    # Verify
    inspector = inspect(engine)
    columns = inspector.get_columns('discount_rates')
    column_names = [col['name'] for col in columns]
    print(f"Updated discount_rates columns: {column_names}")

if __name__ == "__main__":
    check_and_add_threshold_amount()
