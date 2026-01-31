"""Seed initial master data into the database."""
import os
import sys

# Set DATABASE_URL for Neon PostgreSQL
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_I7YCoVX5ajmL@ep-young-fog-a1v5j4i7-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

from sqlalchemy.orm import Session
from database import engine, get_db
from models import Base, SalesPerson, Product, Contractor, TaxRate, DiscountRate

def seed_data():
    """Insert initial master data."""
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
    
    try:
        # Check if data already exists
        existing_sp = db.query(SalesPerson).count()
        if existing_sp > 0:
            print(f"Data already exists ({existing_sp} sales persons). Skipping seed.")
            return
        
        # 販売員データ (34名)
        sales_persons_data = [
            (1, "平田 雄里", False),
            (2, "水口 千春", False),
            (3, "石田 美樹", False),
            (4, "板澤 かすみ", False),
            (5, "伝法谷 由紀", False),
            (6, "藤澤 玲子", True),   # 削除フラグ
            (7, "大島 純子", False),
            (8, "中本 幸子", False),
            (9, "山村 由香", False),
            (10, "渡邉 麻衣子", False),
            (11, "西邑 ひとみ", False),
            (12, "藤谷 友佳里", False),
            (13, "馬渡 知子", False),
            (14, "田村 喜美代", False),
            (15, "安井眞由美", False),
            (16, "千枝 笑子", False),
            (17, "藤盛 貞子", False),
            (18, "神田 めぐみ", False),
            (19, "中島 奈緒美", False),
            (20, "下山 薫", False),
            (21, "竹坂 公希", False),
            (22, "株式会社 正晃", False),
            (23, "熊田商店", False),
            (24, "松久 陽子", False),
            (25, "加賀 文恵", False),
            (26, "大井  恵子", False),
            (27, "岩橋智子", False),
            (28, "工藤ひろみ", False),
            (29, "東麻衣子", False),
            (30, "丸美ヶ丘温泉", False),
            (31, "大島 淳一", False),
            (32, "後藤 希", False),
            (33, "樋口 洋子", False),
            (34, "千田商店", False),
        ]
        
        for sp_id, name, deleted in sales_persons_data:
            db.add(SalesPerson(id=sp_id, name=name, deleted_flag=deleted))
        
        print(f"✓ Added {len(sales_persons_data)} sales persons")
        
        # 商品データ (39品目) - 美容関連商品
        products_data = [
            ("ハイシャンプー", 2500),
            ("リンス＆ヘアパック", 2800),
            ("トリートメント", 3000),
            ("ヘアオイル", 1800),
            ("ヘアミスト", 1500),
            ("スタイリングジェル", 1200),
            ("ヘアワックス", 1400),
            ("カラーリング剤", 4500),
            ("パーマ液", 3500),
            ("ブリーチ剤", 2800),
            ("縮毛矯正剤", 5000),
            ("育毛剤", 6000),
            ("スカルプシャンプー", 3200),
            ("ヘッドスパ用品", 2500),
            ("フェイスクリーム", 4000),
            ("化粧水", 2500),
            ("乳液", 2800),
            ("美容液", 5500),
            ("クレンジング", 2000),
            ("洗顔料", 1500),
            ("パック", 800),
            ("リップクリーム", 500),
            ("ファンデーション", 3500),
            ("アイシャドウ", 2000),
            ("マスカラ", 1800),
            ("アイライナー", 1200),
            ("口紅", 2500),
            ("チーク", 1800),
            ("ネイルカラー", 800),
            ("除光液", 400),
            ("ネイルケアセット", 2500),
            ("ボディローション", 2000),
            ("ハンドクリーム", 800),
            ("ボディソープ", 1200),
            ("入浴剤", 600),
            ("アロマオイル", 1500),
            ("マッサージオイル", 2500),
            ("サプリメント", 3000),
            ("ドリンク", 350),
        ]
        
        for i, (name, price) in enumerate(products_data):
            db.add(Product(name=name, price=price, display_order=i+1))
        
        print(f"✓ Added {len(products_data)} products")
        
        # 委託先データ (5社)
        contractors = [
            "株式会社ビューティーサプライ",
            "美容商事株式会社",
            "コスメティック販売",
            "ヘアケア卸売センター",
            "全国美容材料"
        ]
        
        for name in contractors:
            db.add(Contractor(name=name))
        
        print(f"✓ Added {len(contractors)} contractors")
        
        # 税率データ (1件: 10%)
        db.add(TaxRate(rate=10.0, display_name="10%"))
        print("✓ Added 1 tax rate (10%)")
        
        # 割引率データ (5段階)
        discount_rates = [
            (0.0, 0),      # 0%
            (10.0, 21000),  # 10% - 21,000円以上
            (20.0, 42000),  # 20% - 42,000円以上
            (30.0, 200000), # 30% - 200,000円以上
            (40.0, 400000), # 40% - 400,000円以上
        ]
        
        for rate, threshold in discount_rates:
            db.add(DiscountRate(rate=rate, threshold_amount=threshold))
        
        print(f"✓ Added {len(discount_rates)} discount rates")
        
        db.commit()
        print("\n✅ All seed data inserted successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
