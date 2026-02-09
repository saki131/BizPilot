"""委託先請求書用の割引率を追加するスクリプト"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from models import DiscountRate

def add_contractor_discount_rates():
    """割引率マスタに委託先請求書用のデータを追加"""
    db = SessionLocal()
    try:
        # 既存の委託先用割引率を確認
        existing_contractor_rates = db.query(DiscountRate).filter(
            DiscountRate.sales_person_flag == False
        ).count()
        
        if existing_contractor_rates > 0:
            print(f"委託先用割引率は既に{existing_contractor_rates}件存在します。")
            response = input("既存の委託先用割引率を削除して再投入しますか？ (y/n): ")
            if response.lower() == 'y':
                db.query(DiscountRate).filter(
                    DiscountRate.sales_person_flag == False
                ).delete()
                db.commit()
                print("既存の委託先用割引率を削除しました。")
            else:
                print("処理を中止します。")
                return

        # 委託先請求書用の割引率を追加
        contractor_rates = [
            {"rate": 0.20, "threshold_amount": 0, "sales_person_flag": False},
            {"rate": 0.30, "threshold_amount": 200000, "sales_person_flag": False},
            {"rate": 0.40, "threshold_amount": 400000, "sales_person_flag": False},
        ]

        for dr in contractor_rates:
            discount_rate = DiscountRate(**dr)
            db.add(discount_rate)

        db.commit()
        print(f"委託先用割引率を{len(contractor_rates)}件追加しました。")

        # 確認
        print("\n現在の割引率一覧:")
        all_rates = db.query(DiscountRate).order_by(
            DiscountRate.sales_person_flag.desc(),
            DiscountRate.threshold_amount
        ).all()
        
        for rate in all_rates:
            flag_type = "販売員" if rate.sales_person_flag else "委託先"
            print(f"  - ID: {rate.id}, 割引率: {rate.rate}%, 下限額: ¥{rate.threshold_amount:,}, 種別: {flag_type}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_contractor_discount_rates()
