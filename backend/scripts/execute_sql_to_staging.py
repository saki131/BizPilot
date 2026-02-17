#!/usr/bin/env python3
"""
Fly.io staging環境のデータベースに直接SQLを実行
環境変数DATABASE_URLまたはコマンドライン引数で接続情報を指定
"""
import os
import sys
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("エラー: psycopg2がインストールされていません")
    print("インストール: pip install psycopg2-binary")
    sys.exit(1)

SQL_FILE = Path(__file__).parent.parent / 'sql' / 'delivery_notes_insert.sql'

def main():
    # DATABASE_URLを取得
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    else:
        database_url = os.getenv('STAGING_DATABASE_URL') or os.getenv('DATABASE_URL')
    
    if not database_url:
        print("使用方法:")
        print("  1. 環境変数で指定: set STAGING_DATABASE_URL=postgresql://...")
        print("  2. 引数で指定: python execute_sql_staging.py 'postgresql://...'")
        print("\nFly.ioからDATABASE_URLを取得:")
        print("  flyctl ssh console -a bizpilot-backend-staging")
        print("  echo $DATABASE_URL")
        sys.exit(1)
    
    print(f"SQLファイル: {SQL_FILE}")
    print(f"ファイルサイズ: {SQL_FILE.stat().st_size / 1024:.1f} KB")
    
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"\nデータベース接続中...")
    print(f"URL: {database_url[:50]}...")
    
    try:
        conn = psycopg2.connect(database_url, connect_timeout=30)
        cursor = conn.cursor()
        
        print("\nSQL実行中... (数分かかる場合があります)")
        cursor.execute(sql)
        
        affected_rows = cursor.rowcount
        print(f"\n✓ 実行完了")
        print(f"  影響を受けた行数: {affected_rows}")
        
        conn.commit()
        
        # データ確認
        cursor.execute("SELECT COUNT(*) FROM delivery_notes")
        notes_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM delivery_note_details")
        details_count = cursor.fetchone()[0]
        
        print(f"\nデータ確認:")
        print(f"  delivery_notes: {notes_count} 件")
        print(f"  delivery_note_details: {details_count} 件")
        
        cursor.close()
        conn.close()
        
        print("\n✓ 全てのデータが正常に投入されました")
        
    except psycopg2.Error as e:
        print(f"\nデータベースエラー: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\nエラー: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
