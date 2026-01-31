"""Clear sales persons and reseed with correct data."""
import os
import sys

# Set DATABASE_URL for Neon PostgreSQL
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_I7YCoVX5ajmL@ep-young-fog-a1v5j4i7-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

from sqlalchemy.orm import Session
from database import get_db
from models import SalesPerson

def clear_and_reseed():
    """Clear existing sales persons and reseed with correct data."""
    db = next(get_db())
    
    try:
        # Delete all existing sales persons
        deleted_count = db.query(SalesPerson).delete()
        print(f"🗑️  Deleted {deleted_count} existing sales persons")
        
        # 販売員データ (34名) - 正しいデータ
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
        
        db.commit()
        print(f"✅ Added {len(sales_persons_data)} sales persons with correct data")
        
        # Verify
        total = db.query(SalesPerson).count()
        active = db.query(SalesPerson).filter_by(deleted_flag=False).count()
        deleted = db.query(SalesPerson).filter_by(deleted_flag=True).count()
        
        print(f"\n📊 Database status:")
        print(f"  Total: {total}")
        print(f"  Active: {active}")
        print(f"  Deleted: {deleted}")
        
        # Show all sales persons
        print(f"\n📋 Sales persons list:")
        all_sp = db.query(SalesPerson).order_by(SalesPerson.id).all()
        for sp in all_sp:
            flag = "❌" if sp.deleted_flag else "✓"
            print(f"  {flag} ID {sp.id:2d}: {sp.name}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clear_and_reseed()
