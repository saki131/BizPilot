#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""シンプルなマスタデータ投入スクリプト"""
import sys
from database import SessionLocal
from models import User, SalesPerson, Product, Contractor, TaxRate, DiscountRate

# 事前にハッシュ化されたパスワード（admin123）
ADMIN_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWpQkn.U84i"

def init_data():
    db = SessionLocal()
    try:
        # ユーザー
        db.add(User(username="admin", hashed_password=ADMIN_HASH, deleted_flag=False))
        
        # 税率
        db.add(TaxRate(rate=0.10, display_name="10%", deleted_flag=False))
        
        # 割引率（販売員向け）
        db.add(DiscountRate(rate=0.00, threshold_amount=0, customer_flag=True, deleted_flag=False))
        db.add(DiscountRate(rate=0.10, threshold_amount=0, customer_flag=True, deleted_flag=False))
        db.add(DiscountRate(rate=0.20, threshold_amount=42000, customer_flag=True, deleted_flag=False))
        db.add(DiscountRate(rate=0.30, threshold_amount=200000, customer_flag=True, deleted_flag=False))
        db.add(DiscountRate(rate=0.40, threshold_amount=400000, customer_flag=True, deleted_flag=False))
        
        # 割引率（委託先向け）
        db.add(DiscountRate(rate=0.00, threshold_amount=0, customer_flag=False, deleted_flag=False))
        db.add(DiscountRate(rate=0.10, threshold_amount=0, customer_flag=False, deleted_flag=False))
        db.add(DiscountRate(rate=0.20, threshold_amount=42000, customer_flag=False, deleted_flag=False))
        
        # 商品
        db.add(Product(name="サンプル商品A", price=1000, discount_exclusion_flag=False, quota_exclusion_flag=False, quota_target_flag=True, display_order=1, deleted_flag=False))
        db.add(Product(name="サンプル商品B", price=2000, discount_exclusion_flag=False, quota_exclusion_flag=False, quota_target_flag=True, display_order=2, deleted_flag=False))
        db.add(Product(name="サンプル商品C（割引対象外）", price=3000, discount_exclusion_flag=True, quota_exclusion_flag=False, quota_target_flag=False, display_order=3, deleted_flag=False))
        
        # 販売員
        db.add(SalesPerson(name="販売員A", deleted_flag=False))
        db.add(SalesPerson(name="販売員B", deleted_flag=False))
        
        # 委託先
        db.add(Contractor(name="委託先A", deleted_flag=False))
        db.add(Contractor(name="委託先B", deleted_flag=False))
        
        db.commit()
        print("✅ マスタデータ投入完了")
        return 0
    except Exception as e:
        print(f"❌ エラー: {e}")
        db.rollback()
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(init_data())
