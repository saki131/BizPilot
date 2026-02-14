#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""シンプルなマスタデータ投入スクリプト"""
import sys
from database import SessionLocal
from models import User, SalesPerson, Product, Contractor, TaxRate, DiscountRate

# 事前にハッシュ化されたパスワード
ADMIN_HASH = "$2b$12$8CE.0fRvw0Zz3QxjZrucgOl5tTdSBYFt1vtFOIym82su8qL.T6c06"  # password123
KAZUMI_HASH = "$2b$12$M6dJyysfFvYebLoyrV2p4OuCH777uwIYVHjyHrHTe8e5BohJW8OdO"  # kazumi/1431

def init_data():
    db = SessionLocal()
    try:
        # ユーザー（既存をチェック）
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            db.add(User(user_id=1, username="admin", hashed_password=ADMIN_HASH, deleted_flag=False))
            print("✅ adminユーザーを作成しました")
        else:
            print("ℹ️  adminユーザーは既に存在します")
        
        existing_kazumi = db.query(User).filter(User.username == "kazumi").first()
        if not existing_kazumi:
            db.add(User(user_id=2, username="kazumi", hashed_password=KAZUMI_HASH, deleted_flag=False))
            print("✅ kazumiユーザーを作成しました")
        else:
            print("ℹ️  kazumiユーザーは既に存在します")
        
        # 税率（既存をチェック）
        existing_tax = db.query(TaxRate).first()
        if not existing_tax:
            db.add(TaxRate(tax_rate_id=1, rate=0.10, display_name="10%", deleted_flag=False))
            print("✅ 税率を作成しました")
        else:
            print("ℹ️  税率は既に存在します")
        
        # 既存のマスタデータを削除
        print("🗑️  既存のマスタデータを削除中...")
        db.query(SalesPerson).delete()
        db.query(Product).delete()
        db.query(Contractor).delete()
        db.query(DiscountRate).delete()
        print("✅ 既存のマスタデータを削除しました")
        
        # 割引率（CSVデータを反映、sales_person_flagに変更）
        db.add(DiscountRate(discount_rate_id=1, rate=0.00, threshold_amount=0, sales_person_flag=True, deleted_flag=False))
        db.add(DiscountRate(discount_rate_id=2, rate=0.10, threshold_amount=0, sales_person_flag=True, deleted_flag=False))
        db.add(DiscountRate(discount_rate_id=3, rate=0.20, threshold_amount=42000, sales_person_flag=True, deleted_flag=False))
        db.add(DiscountRate(discount_rate_id=4, rate=0.30, threshold_amount=200000, sales_person_flag=True, deleted_flag=False))
        db.add(DiscountRate(discount_rate_id=5, rate=0.40, threshold_amount=400000, sales_person_flag=True, deleted_flag=False))
        db.add(DiscountRate(discount_rate_id=6, rate=0.20, threshold_amount=0, sales_person_flag=False, deleted_flag=False))
        db.add(DiscountRate(discount_rate_id=7, rate=0.30, threshold_amount=200000, sales_person_flag=False, deleted_flag=False))
        db.add(DiscountRate(discount_rate_id=8, rate=0.40, threshold_amount=400000, sales_person_flag=False, deleted_flag=False))
        
        # 販売員
        sales_persons = [
            (1, "平田 雄里", False, 1), (2, "水口 千春", False, 2), (3, "石田 美樹", False, 3), (4, "板澤 かすみ", False, 4),
            (5, "伝法谷 由紀", False, 5), (6, "藤澤 玲子", True, 6), (7, "大島 純子", False, 7), (8, "中本 幸子", False, 8),
            (9, "山村 由香", False, 9), (10, "渡邉 麻衣子", False, 10), (11, "西邑 ひとみ", False, 11), (12, "藤谷 友佳里", False, 12),
            (13, "馬渡 知子", False, 13), (14, "田村 喜美代", False, 14), (15, "安井眞由美", False, 15), (16, "千枝 笑子", False, 16),
            (17, "藤盛 貞子", False, 17), (18, "神田 めぐみ", False, 18), (19, "中島 奈緒美", False, 19), (20, "下山 薫", False, 20),
            (21, "竹坂 公希", False, 21), (22, "株式会社 正晃", False, 22), (23, "熊田商店", False, 23), (24, "松久 陽子", False, 24),
            (25, "加賀 文恵", False, 25), (26, "大井  恵子", False, 26), (27, "岩橋智子", False, 27), (28, "工藤ひろみ", False, 28),
            (29, "東麻衣子", False, 29), (30, "丸美ケ丘温泉", False, 30), (31, "大島 淳一", False, 31), (32, "後藤 希", False, 32),
            (33, "樋口 洋子", False, 33), (34, "千田商店", False, 34)
        ]
        for sp_id, name, deleted, order in sales_persons:
            db.add(SalesPerson(sales_person_id=sp_id, name=name, deleted_flag=deleted, display_order=order))
        
        # 商品
        products = [
            (1, "ソープ", 1200, False, False, True, False, 1),
            (2, "クレンジング", 3000, False, False, True, False, 2),
            (3, "スキンローション", 3000, False, False, True, False, 3),
            (4, "メディカローション", 3000, False, False, True, False, 4),
            (5, "美肌冠", 3500, False, True, False, False, 5),
            (6, "V8ローション", 5000, False, True, False, False, 6),
            (7, "美肌クリーム", 3000, False, False, True, False, 7),
            (8, "あれ肌クリーム", 3000, False, False, True, False, 8),
            (9, "アクアカラー①", 3000, False, True, False, False, 9),
            (10, "アクアカラー②", 3000, False, True, False, False, 10),
            (11, "アクアカラー③", 3000, False, True, False, False, 11),
            (12, "ハイシャンプー", 2500, False, False, True, False, 12),
            (13, "リンス＆ヘアパック", 2500, False, False, True, False, 13),
            (14, "ハイシャンプー（2300円）", 2300, False, False, True, True, 14),
            (15, "リンス＆ヘアパック（2300円）", 2300, False, False, True, True, 15),
            (16, "ハイデール", 5000, False, False, True, False, 16),
            (17, "プレストパウダー", 3000, False, False, True, False, 17),
            (18, "リップスティック10", 3000, False, False, True, False, 18),
            (19, "リップスティック50", 3000, False, False, True, False, 19),
            (20, "2wayファンデーション80", 4500, False, False, True, False, 20),
            (21, "2wayファンデーション100", 4500, False, False, True, False, 21),
            (22, "2wayファンデーション200", 4500, False, False, True, False, 22),
            (23, "2wayファンデーション300", 4500, False, False, True, False, 23),
            (24, "2wayファンデーション400", 4500, False, False, True, False, 24),
            (25, "2wayファンデーションリフィル80", 3000, False, False, True, False, 25),
            (26, "2wayファンデーションリフィル100", 3000, False, False, True, False, 26),
            (27, "2wayファンデーションリフィル200", 3000, False, False, True, False, 27),
            (28, "2wayファンデーションリフィル300", 3000, False, False, True, False, 28),
            (29, "2wayファンデーションリフィル400", 3000, False, False, True, False, 29),
            (30, "サンプル（ソープ美肌）", 100, True, False, False, False, 30),
            (31, "サンプル（あれ肌）", 50, True, False, False, False, 31),
            (32, "サンプル（スキン）", 50, True, False, False, False, 32),
            (33, "サンプル（リムーバー）", 50, True, False, False, False, 33),
            (34, "サンプル（アクア①）", 100, True, False, False, False, 34),
            (35, "サンプル（アクア②）", 100, True, False, False, False, 35),
            (36, "サンプル（アクア③）", 100, True, False, False, False, 36),
            (37, "紙袋（手付き）", 100, True, False, False, False, 37),
            (38, "紙袋", 10, True, False, False, False, 38),
            (39, "マニュアル", 500, True, False, False, False, 39),
        ]
        for prod_id, name, price, disc_excl, quota_excl, quota_tgt, deleted, order in products:
            db.add(Product(product_id=prod_id, name=name, price=price, discount_exclusion_flag=disc_excl, 
                         quota_exclusion_flag=quota_excl, quota_target_flag=quota_tgt, 
                         deleted_flag=deleted, display_order=order))
        
        # 委託先
        contractors = [
            (1, "すがの", False, 1), (2, "193スタイル", False, 2), (3, "ふれあい", False, 3),
            (4, "熊田商店", False, 4), (5, "丸美ケ丘温泉", False, 5)
        ]
        for cont_id, name, deleted, order in contractors:
            db.add(Contractor(contractor_id=cont_id, name=name, deleted_flag=deleted, display_order=order))
        
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
