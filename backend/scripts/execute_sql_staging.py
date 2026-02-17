#!/usr/bin/env python3
"""
Staging環境のデータベースにSQLを実行するスクリプト
"""
import os
import sys
from pathlib import Path

# SQLファイルのパス
SQL_FILE = Path(__file__).parent.parent / 'sql' / 'delivery_notes_insert.sql'

def main():
    # DATABASE_URLを環境変数から取得
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("エラー: DATABASE_URL環境変数が設定されていません")
        print("\nFly.ioのシークレットから取得してください:")
        print("  flyctl secrets list -a bizpilot-backend-staging")
        sys.exit(1)
    
    try:
        import psycopg2
    except ImportError:
        print("エラー: psycopg2がインストールされていません")
        print("  pip install psycopg2-binary")
        sys.exit(1)
    
    print(f"SQLファイル読み込み: {SQL_FILE}")
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"データベース接続: {database_url[:30]}...")
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("SQL実行中...")
        cursor.execute(sql)
        
        print(f"✓ 実行完了")
        print(f"  - delivery_notes: INSERT完了")
        print(f"  - delivery_note_details: INSERT完了")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✓ 全てのデータが正常に投入されました")
        
    except Exception as e:
        print(f"\nエラー発生: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)

if __name__ == '__main__':
    main()
