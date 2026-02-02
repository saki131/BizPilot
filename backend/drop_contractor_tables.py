"""Drop contractor invoice tables"""
from database import get_db
from sqlalchemy import text

db = next(get_db())
db.execute(text('DROP TABLE IF EXISTS contractor_invoice_details CASCADE'))
db.execute(text('DROP TABLE IF EXISTS contractor_invoices CASCADE'))
db.commit()
print('Tables dropped successfully')
