#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""discount_ratesテーブルのcustomer_flagをsales_person_flagに変更"""
from sqlalchemy import create_engine, text
import os

# データベース接続
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("エラー: DATABASE_URLが設定されていません")
    exit(1)

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # カラム名を変更
        conn.execute(text("""
            ALTER TABLE discount_rates 
            RENAME COLUMN customer_flag TO sales_person_flag;
        """))
        conn.commit()
        print("✅ カラム名を変更しました: customer_flag → sales_person_flag")
except Exception as e:
    print(f"エラー: {e}")
    # カラムが既に存在する場合は成功とみなす
    if "does not exist" in str(e):
        print("ℹ️  customer_flagカラムが見つかりません。既に変更済みの可能性があります")
    elif "already exists" in str(e):
        print("ℹ️  sales_person_flagカラムが既に存在します")
