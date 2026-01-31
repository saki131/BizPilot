#!/usr/bin/env python3
"""Fix invoice discount rate IDs"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import SalesInvoice, DiscountRate

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bizpilot")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Get invoices with invalid discount_rate_id
    invoices = db.query(SalesInvoice).all()
    
    # Get valid discount rates
    rate_0 = db.query(DiscountRate).filter(DiscountRate.rate == 0.00, DiscountRate.customer_flag == True).first()
    rate_10 = db.query(DiscountRate).filter(DiscountRate.rate == 0.10, DiscountRate.customer_flag == True).first()
    
    print(f"Valid rates: 0%=ID{rate_0.id if rate_0 else 'N/A'}, 10%=ID{rate_10.id if rate_10 else 'N/A'}")
    print()
    
    for inv in invoices:
        discount_rate = db.query(DiscountRate).filter(DiscountRate.id == inv.discount_rate_id).first()
        if not discount_rate:
            print(f"Invoice {inv.id}: Invalid discount_rate_id={inv.discount_rate_id}")
            # Check discount amount to guess intended rate
            if inv.quota_discount_amount > 0 or inv.non_quota_discount_amount > 0:
                # Has discount, likely 10%
                if rate_10:
                    print(f"  -> Updating to ID={rate_10.id} (10%)")
                    inv.discount_rate_id = rate_10.id
            else:
                # No discount, likely 0%
                if rate_0:
                    print(f"  -> Updating to ID={rate_0.id} (0%)")
                    inv.discount_rate_id = rate_0.id
    
    db.commit()
    print("\nDone!")
    
finally:
    db.close()
