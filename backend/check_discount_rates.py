#!/usr/bin/env python3
"""Check discount rates in database"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import DiscountRate

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bizpilot")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    print("=== Discount Rates ===")
    rates = db.query(DiscountRate).order_by(DiscountRate.threshold_amount).all()
    for rate in rates:
        print(f"ID: {rate.id}, Rate: {rate.rate} ({type(rate.rate).__name__}), Threshold: {rate.threshold_amount}, Customer: {rate.customer_flag}")
        print(f"  Rate as float: {float(rate.rate)}")
        print(f"  Rate * 100: {float(rate.rate) * 100}")
        print()
finally:
    db.close()
