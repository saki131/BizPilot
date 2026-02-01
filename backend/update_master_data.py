"""マスタデータ更新スクリプト - 商品、委託先、販売員のデータを正しい値に修正"""
import sys
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Product, SalesPerson, Contractor

def update_products(db: Session):
    """商品テーブルのデータを更新"""
    print("Updating products...")
    
    # 商品データ定義
    products_data = [
        # ID, 商品名, 単価, 割引対象外, ノルマ対象外, ノルマ対象, 削除フラグ, 表示順
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
        (12, "ハイシャンプー（2300円）", 2300, False, False, True, True, 14),
        (13, "リンス＆ヘアパック（2300円）", 2300, False, False, True, True, 15),
        (14, "ハイデール", 5000, False, False, True, False, 16),
        (15, "プレストパウダー", 3000, False, False, True, False, 17),
        (16, "リップスティック10", 3000, False, False, True, False, 18),
        (17, "リップスティック50", 3000, False, False, True, False, 19),
        (18, "2wayファンデーション80", 4500, False, False, True, False, 20),
        (19, "2wayファンデーション100", 4500, False, False, True, False, 21),
        (20, "2wayファンデーション200", 4500, False, False, True, False, 22),
        (21, "2wayファンデーション300", 4500, False, False, True, False, 23),
        (22, "2wayファンデーション400", 4500, False, False, True, False, 24),
        (23, "2wayファンデーションリフィル80", 3000, False, False, True, False, 25),
        (24, "2wayファンデーションリフィル100", 3000, False, False, True, False, 26),
        (25, "2wayファンデーションリフィル200", 3000, False, False, True, False, 27),
        (26, "2wayファンデーションリフィル300", 3000, False, False, True, False, 28),
        (27, "2wayファンデーションリフィル400", 3000, False, False, True, False, 29),
        (28, "サンプル（ソープ美肌）", 100, True, False, False, False, 30),
        (29, "サンプル（あれ肌）", 50, True, False, False, False, 31),
        (30, "サンプル（スキン）", 50, True, False, False, False, 32),
        (31, "サンプル（リムーバー）", 50, True, False, False, False, 33),
        (32, "サンプル（アクア①）", 100, True, False, False, False, 34),
        (33, "サンプル（アクア②）", 100, True, False, False, False, 35),
        (34, "サンプル（アクア③）", 100, True, False, False, False, 36),
        (35, "紙袋（手付き）", 100, True, False, False, False, 37),
        (36, "紙袋", 10, True, False, False, False, 38),
        (37, "マニュアル", 500, True, False, False, False, 39),
        (38, "ハイシャンプー", 2500, False, False, True, False, 12),
        (39, "リンス＆ヘアパック", 2500, False, False, True, False, 13),
    ]
    
    updated_count = 0
    created_count = 0
    
    for product_data in products_data:
        product_id, name, price, discount_excl, non_quota, quota_target, deleted, display_order = product_data
        
        # 既存の商品を検索
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if product:
            # 更新
            product.name = name
            product.price = price
            product.discount_exclusion_flag = discount_excl
            product.non_quota_target_flag = non_quota
            product.quota_target_flag = quota_target
            product.deleted_flag = deleted
            product.display_order = display_order
            updated_count += 1
            print(f"  Updated: {product_id} - {name}")
        else:
            # 新規作成
            product = Product(
                id=product_id,
                name=name,
                price=price,
                discount_exclusion_flag=discount_excl,
                non_quota_target_flag=non_quota,
                quota_target_flag=quota_target,
                deleted_flag=deleted,
                display_order=display_order
            )
            db.add(product)
            created_count += 1
            print(f"  Created: {product_id} - {name}")
    
    db.commit()
    print(f"\nProducts: {updated_count} updated, {created_count} created")


def update_sales_persons(db: Session):
    """販売員テーブルのデータを更新"""
    print("\nUpdating sales persons (販売員)...")
    
    # 販売員データ定義
    sales_persons_data = [
        # ID, 販売員名, 削除フラグ
        (1, "平田 雄里", False),
        (2, "水口 千春", False),
        (3, "石田 美樹", False),
        (4, "板澤 かすみ", False),
        (5, "伝法谷 由紀", False),
        (6, "藤澤 玲子", True),
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
    
    updated_count = 0
    created_count = 0
    
    for sp_data in sales_persons_data:
        sp_id, name, deleted = sp_data
        
        # 既存の販売員を検索
        sales_person = db.query(SalesPerson).filter(SalesPerson.id == sp_id).first()
        
        if sales_person:
            # 更新
            sales_person.name = name
            sales_person.deleted_flag = deleted
            updated_count += 1
            print(f"  Updated: {sp_id} - {name}")
        else:
            # 新規作成
            sales_person = SalesPerson(
                id=sp_id,
                name=name,
                deleted_flag=deleted
            )
            db.add(sales_person)
            created_count += 1
            print(f"  Created: {sp_id} - {name}")
    
    db.commit()
    print(f"\nSales Persons: {updated_count} updated, {created_count} created")


def update_contractors(db: Session):
    """委託先テーブルのデータを更新"""
    print("\nUpdating contractors (委託先)...")
    
    # 委託先データ定義
    contractors_data = [
        # ID, 委託先名, 削除フラグ
        (1, "すがの", False),
        (2, "193スタイル", False),
        (3, "ふれあい", False),
        (4, "熊田商店", False),
        (5, "丸美ヶ丘温泉", False),
    ]
    
    updated_count = 0
    created_count = 0
    
    for contractor_data in contractors_data:
        contractor_id, name, deleted = contractor_data
        
        # 既存の委託先を検索
        contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
        
        if contractor:
            # 更新
            contractor.name = name
            contractor.deleted_flag = deleted
            updated_count += 1
            print(f"  Updated: {contractor_id} - {name}")
        else:
            # 新規作成
            contractor = Contractor(
                id=contractor_id,
                name=name,
                deleted_flag=deleted
            )
            db.add(contractor)
            created_count += 1
            print(f"  Created: {contractor_id} - {name}")
    
    db.commit()
    print(f"\nContractors: {updated_count} updated, {created_count} created")


def main():
    """メイン処理"""
    print("=" * 60)
    print("マスタデータ更新スクリプト")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 商品データ更新
        update_products(db)
        
        # 販売員データ更新
        update_sales_persons(db)
        
        # 委託先データ更新
        update_contractors(db)
        
        print("\n" + "=" * 60)
        print("✓ マスタデータの更新が完了しました")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ エラーが発生しました: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
