#!/usr/bin/env python3
"""Check discount rate ID=2"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import DiscountRate

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bizpilot")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    rate = db.query(DiscountRate).filter(DiscountRate.id == 2).first()
    if rate:
        print(f"ID=2: rate={rate.rate}, threshold={rate.threshold_amount}, customer_flag={rate.customer_flag}, deleted_flag={rate.deleted_flag}")
        print(f"  rate as float: {float(rate.rate)}")
    else:
        print("ID=2: NOT FOUND")
finally:
    db.close()
