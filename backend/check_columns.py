#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""discount_ratesテーブルのカラムを確認"""
from database import engine
from sqlalchemy import inspect

insp = inspect(engine)
cols = insp.get_columns('discount_rates')
print("discount_ratesテーブルのカラム:")
for col in cols:
    print(f"  - {col['name']} ({col['type']})")
