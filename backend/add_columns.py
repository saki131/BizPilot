"""Add missing columns to sales_invoices table."""
from sqlalchemy import text
from database import SessionLocal

def add_columns():
    db = SessionLocal()
    try:
        # Add columns if not exists
        db.execute(text("""
            ALTER TABLE sales_invoices 
            ADD COLUMN IF NOT EXISTS invoice_date DATE NULL,
            ADD COLUMN IF NOT EXISTS receipt_date DATE NULL,
            ADD COLUMN IF NOT EXISTS non_discountable_amount INTEGER DEFAULT 0 NOT NULL,
            ADD COLUMN IF NOT EXISTS note VARCHAR(500) NULL
        """))
        db.commit()
        print("Columns added successfully!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_columns()
