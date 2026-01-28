"""割引率の値を修正するスクリプト"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from models import DiscountRate

def update_discount_rates():
    """割引率の値を10.00 → 0.10のように修正"""
    db = SessionLocal()
    try:
        # 全割引率を取得
        rates = db.query(DiscountRate).all()
        
        print(f"割引率マスタの修正を開始します。({len(rates)}件)")
        
        for rate in rates:
            old_value = float(rate.rate)
            # 10.00以上の値は100で割る（10.00 → 0.10、20.00 → 0.20）
            if old_value >= 1.0:
                new_value = old_value / 100
                print(f"ID {rate.id}: {old_value} → {new_value}")
                rate.rate = new_value
        
        db.commit()
        print("\n修正が完了しました。")
        
        # 確認
        print("\n修正後の割引率:")
        for rate in db.query(DiscountRate).all():
            flag_type = "販売員" if rate.customer_flag else "委託先"
            print(f"  - ID: {rate.id}, 割引率: {float(rate.rate)*100}%, 下限額: ¥{rate.threshold_amount:,}, 種別: {flag_type}")
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_discount_rates()
