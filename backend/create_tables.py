"""Create sales_invoices table directly."""
from sqlalchemy import text
from database import SessionLocal

def create_sales_invoices():
    db = SessionLocal()
    try:
        # Create sales_invoices table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS sales_invoices (
                id SERIAL PRIMARY KEY,
                sales_person_id INTEGER NOT NULL REFERENCES sales_persons(id),
                invoice_number VARCHAR(50) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                discount_rate_id INTEGER NOT NULL REFERENCES discount_rates(id),
                invoice_date DATE NULL,
                receipt_date DATE NULL,
                non_discountable_amount INTEGER DEFAULT 0 NOT NULL,
                note VARCHAR(500) NULL,
                quota_subtotal INTEGER DEFAULT 0 NOT NULL,
                quota_discount_amount INTEGER DEFAULT 0 NOT NULL,
                quota_total INTEGER DEFAULT 0 NOT NULL,
                non_quota_subtotal INTEGER DEFAULT 0 NOT NULL,
                non_quota_discount_amount INTEGER DEFAULT 0 NOT NULL,
                non_quota_total INTEGER DEFAULT 0 NOT NULL,
                total_amount_ex_tax INTEGER DEFAULT 0 NOT NULL,
                tax_amount INTEGER DEFAULT 0 NOT NULL,
                total_amount_inc_tax INTEGER DEFAULT 0 NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Create index
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_sales_invoices_id ON sales_invoices(id)
        """))
        
        # Create sales_invoice_details table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS sales_invoice_details (
                id SERIAL PRIMARY KEY,
                sales_invoice_id INTEGER NOT NULL REFERENCES sales_invoices(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id),
                total_quantity INTEGER DEFAULT 0 NOT NULL,
                unit_price INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Create index
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_sales_invoice_details_id ON sales_invoice_details(id)
        """))
        
        db.commit()
        print("✅ Tables created successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sales_invoices()
