#!/usr/bin/env python3
"""Check sales invoices in database"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import SalesInvoice, DiscountRate

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bizpilot")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    print("=== Sales Invoices ===")
    invoices = db.query(SalesInvoice).order_by(SalesInvoice.id.desc()).limit(5).all()
    for inv in invoices:
        discount_rate = db.query(DiscountRate).filter(DiscountRate.id == inv.discount_rate_id).first()
        print(f"Invoice ID: {inv.id}")
        print(f"  Discount Rate ID: {inv.discount_rate_id}")
        if discount_rate:
            print(f"  Discount Rate from DB: {discount_rate.rate} ({type(discount_rate.rate).__name__})")
            print(f"  Rate as float: {float(discount_rate.rate)}")
            print(f"  Rate * 100: {float(discount_rate.rate) * 100}")
        print()
finally:
    db.close()
