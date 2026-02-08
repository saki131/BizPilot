# -*- coding: utf-8 -*-
"""マスタデータ投入スクリプト"""
from database import SessionLocal
from models import User, SalesPerson, Product, Contractor, TaxRate, DiscountRate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_master_data():
    """マスタデータを投入"""
    db = SessionLocal()
    
    try:
        # ユーザー
        admin_user = User(
            username="admin",
            hashed_password=pwd_context.hash("admin123"),
            deleted_flag=False
        )
        db.add(admin_user)
        
        # 税率
        tax_rate_10 = TaxRate(
            rate=0.10,
            display_name="10%",
            deleted_flag=False
        )
        db.add(tax_rate_10)
        
        # 割引率（販売員向け）
        discount_rates_sales = [
            DiscountRate(rate=0.00, threshold_amount=0, customer_flag=True, deleted_flag=False),
            DiscountRate(rate=0.10, threshold_amount=0, customer_flag=True, deleted_flag=False),
            DiscountRate(rate=0.20, threshold_amount=42000, customer_flag=True, deleted_flag=False),
            DiscountRate(rate=0.30, threshold_amount=200000, customer_flag=True, deleted_flag=False),
            DiscountRate(rate=0.40, threshold_amount=400000, customer_flag=True, deleted_flag=False),
        ]
        for rate in discount_rates_sales:
            db.add(rate)
        
        # 割引率（委託先向け）
        discount_rates_contractor = [
            DiscountRate(rate=0.00, threshold_amount=0, customer_flag=False, deleted_flag=False),
            DiscountRate(rate=0.10, threshold_amount=0, customer_flag=False, deleted_flag=False),
            DiscountRate(rate=0.20, threshold_amount=42000, customer_flag=False, deleted_flag=False),
        ]
        for rate in discount_rates_contractor:
            db.add(rate)
        
        # サンプル商品
        sample_products = [
            Product(name="サンプル商品A", price=1000, discount_exclusion_flag=False, quota_exclusion_flag=False, quota_target_flag=True, display_order=1, deleted_flag=False),
            Product(name="サンプル商品B", price=2000, discount_exclusion_flag=False, quota_exclusion_flag=False, quota_target_flag=True, display_order=2, deleted_flag=False),
            Product(name="サンプル商品C（割引対象外）", price=3000, discount_exclusion_flag=True, quota_exclusion_flag=False, quota_target_flag=False, display_order=3, deleted_flag=False),
        ]
        for product in sample_products:
            db.add(product)
        
        # サンプル販売員
        sample_sales_persons = [
            SalesPerson(name="販売員A", deleted_flag=False),
            SalesPerson(name="販売員B", deleted_flag=False),
        ]
        for sp in sample_sales_persons:
            db.add(sp)
        
        # サンプル委託先
        sample_contractors = [
            Contractor(name="委託先A", deleted_flag=False),
            Contractor(name="委託先B", deleted_flag=False),
        ]
        for contractor in sample_contractors:
            db.add(contractor)
        
        db.commit()
        print("✅ マスタデータの投入が完了しました")
        print("  - ユーザー: admin / admin123")
        print("  - 税率: 10%")
        print(f"  - 割引率: {len(discount_rates_sales)}件（販売員）, {len(discount_rates_contractor)}件（委託先）")
        print(f"  - 商品: {len(sample_products)}件")
        print(f"  - 販売員: {len(sample_sales_persons)}件")
        print(f"  - 委託先: {len(sample_contractors)}件")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_master_data()
