#!/usr/bin/env python3
"""Check all discount rates including deleted"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import DiscountRate

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bizpilot")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    print("=== ALL Discount Rates (including deleted) ===")
    rates = db.query(DiscountRate).order_by(DiscountRate.id).all()
    for rate in rates:
        deleted = " [DELETED]" if rate.deleted_flag else ""
        print(f"ID: {rate.id}, Rate: {rate.rate}, Threshold: {rate.threshold_amount}, Customer: {rate.customer_flag}, Deleted: {rate.deleted_flag}{deleted}")
finally:
    db.close()
