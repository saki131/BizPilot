"""Check database tables."""
from sqlalchemy import text, inspect
from database import engine

def check_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table}")
    
    # Check if sales_invoices exists
    if 'sales_invoices' in tables:
        print("\nsales_invoices table exists!")
        columns = inspector.get_columns('sales_invoices')
        print(f"Columns ({len(columns)}):")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
    else:
        print("\n❌ sales_invoices table does NOT exist!")

if __name__ == "__main__":
    check_tables()
