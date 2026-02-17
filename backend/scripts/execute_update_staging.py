"""
staging環境のデータベースにUPDATE SQLを実行する
"""
import psycopg2
import os
import sys

def execute_update_sql():
    """UPDATE SQLをstaging DBで実行"""
    
    # DATABASE_URLを環境変数から取得
    database_url = os.environ.get('STAGING_DATABASE_URL')
    if not database_url:
        print("エラー: STAGING_DATABASE_URLが設定されていません")
        sys.exit(1)
    
    # SQLファイルを読み込み
    sql_file = 'c:/Users/Owner/workspace/BizPilot/backend/sql/update_sales_person_ids.sql'
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"SQLファイルを読み込みました: {sql_file}")
    print(f"データベースに接続中...")
    
    try:
        # データベース接続
        conn = psycopg2.connect(database_url, connect_timeout=30)
        cursor = conn.cursor()
        
        print("接続成功")
        
        # 更新前の状態を確認
        cursor.execute("""
            SELECT sales_person_id, COUNT(*) 
            FROM delivery_notes 
            GROUP BY sales_person_id 
            ORDER BY sales_person_id
        """)
        before_counts = cursor.fetchall()
        print("\n更新前の販売員別納品書数:")
        for sp_id, count in before_counts:
            print(f"  販売員ID {sp_id}: {count}件")
        
        # UPDATE SQLを実行
        print("\nUPDATE文を実行中...")
        cursor.execute(sql_content)
        
        # 更新後の状態を確認
        cursor.execute("""
            SELECT sales_person_id, COUNT(*) 
            FROM delivery_notes 
            GROUP BY sales_person_id 
            ORDER BY sales_person_id
        """)
        after_counts = cursor.fetchall()
        print("\n更新後の販売員別納品書数:")
        for sp_id, count in after_counts:
            print(f"  販売員ID {sp_id}: {count}件")
        
        # コミット
        conn.commit()
        print("\n✓ 更新が正常に完了しました")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)

if __name__ == "__main__":
    execute_update_sql()
