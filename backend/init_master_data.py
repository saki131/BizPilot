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
        
        # 割引率
        db.add(DiscountRate(rate=0.00, threshold_amount=0, customer_flag=True, deleted_flag=False))
        db.add(DiscountRate(rate=0.10, threshold_amount=0, customer_flag=True, deleted_flag=False))
        db.add(DiscountRate(rate=0.20, threshold_amount=42000, customer_flag=True, deleted_flag=False))
        db.add(DiscountRate(rate=0.30, threshold_amount=200000, customer_flag=False, deleted_flag=False))
        db.add(DiscountRate(rate=0.40, threshold_amount=400000, customer_flag=False, deleted_flag=False))
        
        # 販売員
        sales_persons = [
            ("平田 雄里", False), ("水口 千春", False), ("石田 美樹", False), ("板澤 かすみ", False),
            ("伝法谷 由紀", False), ("藤澤 玲子", True), ("大島 純子", False), ("中本 幸子", False),
            ("山村 由香", False), ("渡邉 麻衣子", False), ("西邑 ひとみ", False), ("藤谷 友佳里", False),
            ("馬渡 知子", False), ("田村 喜美代", False), ("安井眞由美", False), ("千枝 笑子", False),
            ("藤盛 貞子", False), ("神田 めぐみ", False), ("中島 奈緒美", False), ("下山 薫", False),
            ("竹坂 公希", False), ("株式会社 正晃", False), ("熊田商店", False), ("松久 陽子", False),
            ("加賀 文恵", False), ("大井  恵子", False), ("岩橋智子", False), ("工藤ひろみ", False),
            ("東麻衣子", False), ("丸美ヶ丘温泉", False), ("大島 淳一", False), ("後藤 希", False),
            ("樋口 洋子", False), ("千田商店", False)
        ]
        for name, deleted in sales_persons:
            db.add(SalesPerson(name=name, deleted_flag=deleted))
        
        # 商品
        products = [
            ("ソープ", 1200, False, False, True, False, 1),
            ("クレンジング", 3000, False, False, True, False, 2),
            ("スキンローション", 3000, False, False, True, False, 3),
            ("メディカローション", 3000, False, False, True, False, 4),
            ("美肌冠", 3500, False, True, False, False, 5),
            ("V8ローション", 5000, False, True, False, False, 6),
            ("美肌クリーム", 3000, False, False, True, False, 7),
            ("あれ肌クリーム", 3000, False, False, True, False, 8),
            ("アクアカラー①", 3000, False, True, False, False, 9),
            ("アクアカラー②", 3000, False, True, False, False, 10),
            ("アクアカラー③", 3000, False, True, False, False, 11),
            ("ハイシャンプー", 2500, False, False, True, False, 12),
            ("リンス＆ヘアパック", 2500, False, False, True, False, 13),
            ("ハイシャンプー（2300円）", 2300, False, False, True, True, 14),
            ("リンス＆ヘアパック（2300円）", 2300, False, False, True, True, 15),
            ("ハイデール", 5000, False, False, True, False, 16),
            ("プレストパウダー", 3000, False, False, True, False, 17),
            ("リップスティック10", 3000, False, False, True, False, 18),
            ("リップスティック50", 3000, False, False, True, False, 19),
            ("2wayファンデーション80", 4500, False, False, True, False, 20),
            ("2wayファンデーション100", 4500, False, False, True, False, 21),
            ("2wayファンデーション200", 4500, False, False, True, False, 22),
            ("2wayファンデーション300", 4500, False, False, True, False, 23),
            ("2wayファンデーション400", 4500, False, False, True, False, 24),
            ("2wayファンデーションリフィル80", 3000, False, False, True, False, 25),
            ("2wayファンデーションリフィル100", 3000, False, False, True, False, 26),
            ("2wayファンデーションリフィル200", 3000, False, False, True, False, 27),
            ("2wayファンデーションリフィル300", 3000, False, False, True, False, 28),
            ("2wayファンデーションリフィル400", 3000, False, False, True, False, 29),
            ("サンプル（ソープ美肌）", 100, True, False, False, False, 30),
            ("サンプル（あれ肌）", 50, True, False, False, False, 31),
            ("サンプル（スキン）", 50, True, False, False, False, 32),
            ("サンプル（リムーバー）", 50, True, False, False, False, 33),
            ("サンプル（アクア①）", 100, True, False, False, False, 34),
            ("サンプル（アクア②）", 100, True, False, False, False, 35),
            ("サンプル（アクア③）", 100, True, False, False, False, 36),
            ("紙袋（手付き）", 100, True, False, False, False, 37),
            ("紙袋", 10, True, False, False, False, 38),
            ("マニュアル", 500, True, False, False, False, 39),
        ]
        for name, price, disc_excl, quota_excl, quota_tgt, deleted, order in products:
            db.add(Product(name=name, price=price, discount_exclusion_flag=disc_excl, 
                         quota_exclusion_flag=quota_excl, quota_target_flag=quota_tgt, 
                         deleted_flag=deleted, display_order=order))
        
        # 委託先
        contractors = [
            ("すがの", False), ("193スタイル", False), ("ふれあい", False),
            ("熊田商店", False), ("丸美ヶ丘温泉", False)
        ]
        for name, deleted in contractors:
            db.add(Contractor(name=name, deleted_flag=deleted))
        
        db.commit()
        print("✅ マスタデータ投入完了")
        print(f"  - 販売員: {len(sales_persons)}件")
        print(f"  - 商品: {len(products)}件")
        print(f"  - 委託先: {len(contractors)}件")
        return 0
    except Exception as e:
        print(f"❌ エラー: {e}")
        db.rollback()
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(init_data())
