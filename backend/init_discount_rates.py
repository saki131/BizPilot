"""割引率マスタの初期データ投入スクリプト"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from models import DiscountRate

def init_discount_rates():
    """割引率マスタに初期データを投入"""
    db = SessionLocal()
    try:
        # 既存データを確認
        existing_count = db.query(DiscountRate).count()
        if existing_count > 0:
            print(f"割引率マスタには既に{existing_count}件のデータが存在します。")
            response = input("削除して再投入しますか？ (y/n): ")
            if response.lower() == 'y':
                db.query(DiscountRate).delete()
                db.commit()
                print("既存データを削除しました。")
            else:
                print("処理を中止します。")
                return

        # 販売員請求書用の割引率（0%を追加）
        discount_rates = [
            {"rate": 0.00, "threshold_amount": 0, "customer_flag": True},
            {"rate": 0.10, "threshold_amount": 21000, "customer_flag": True},
            {"rate": 0.20, "threshold_amount": 42000, "customer_flag": True},
            {"rate": 0.30, "threshold_amount": 200000, "customer_flag": True},
            {"rate": 0.40, "threshold_amount": 400000, "customer_flag": True},
            
            # 委託先請求書用の割引率
            {"rate": 0.20, "threshold_amount": 0, "customer_flag": False},
            {"rate": 0.30, "threshold_amount": 200000, "customer_flag": False},
            {"rate": 0.40, "threshold_amount": 400000, "customer_flag": False},
        ]

        for dr in discount_rates:
            discount_rate = DiscountRate(**dr)
            db.add(discount_rate)

        db.commit()
        print(f"割引率マスタに{len(discount_rates)}件のデータを投入しました。")

        # 確認
        print("\n登録された割引率:")
        for rate in db.query(DiscountRate).all():
            flag_type = "販売員" if rate.customer_flag else "委託先"
            print(f"  - ID: {rate.id}, 割引率: {rate.rate}%, 下限額: ¥{rate.threshold_amount:,}, 種別: {flag_type}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_discount_rates()
