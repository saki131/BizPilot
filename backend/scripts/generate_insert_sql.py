#!/usr/bin/env python3
"""
delivery_notes.csv と delivery_note_details.csv から
PostgreSQL INSERT ON CONFLICT 文を生成
"""
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SQL_DIR = BASE_DIR / 'sql'
NOTES_CSV = SQL_DIR / 'delivery_notes.csv'
DETAILS_CSV = SQL_DIR / 'delivery_note_details.csv'
OUTPUT_SQL = SQL_DIR / 'delivery_notes_insert.sql'

def sql_escape(value):
    """値をSQLエスケープ"""
    if value is None or value == '':
        return 'NULL'
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, (int, float)):
        return str(value)
    # 文字列の場合
    return "'" + str(value).replace("'", "''") + "'"

def generate_notes_sql():
    """delivery_notesテーブル用のINSERT文を生成"""
    sqls = []
    sqls.append("-- delivery_notes テーブルへのデータ投入")
    sqls.append("-- 生成日時: " + str(Path(__file__).stat().st_mtime))
    sqls.append("")
    
    with open(NOTES_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cols = [
                'delivery_note_id',
                'sales_person_id',
                'tax_rate_id',
                'quota_amount',
                'non_quota_amount',
                'tax_amount',
                'total_amount_ex_tax',
                'total_amount_inc_tax',
                'remarks',
                'delivery_note_number',
                'file_path',
                'delivery_date',
                'billing_date',
                'image_recognition_data',
                'image_filename',
                'deleted_flag',
                'created_at',
                'updated_at'
            ]
            
            values = [
                sql_escape(row['delivery_note_id']),
                sql_escape(row['sales_person_id']),
                sql_escape(row['tax_rate_id']),
                sql_escape(row['quota_amount']),
                sql_escape(row['non_quota_amount']),
                sql_escape(row['tax_amount']),
                sql_escape(row['total_amount_ex_tax']),
                sql_escape(row['total_amount_inc_tax']),
                sql_escape(row['remarks']),
                sql_escape(row['delivery_note_number']),
                sql_escape(row['file_path']),
                sql_escape(row['delivery_date']),
                sql_escape(row['billing_date']),
                'NULL',  # image_recognition_data
                sql_escape(row['image_filename']),
                sql_escape(row['deleted_flag']),
                sql_escape(row['created_at']),
                sql_escape(row['updated_at'])
            ]
            
            sql = f"""INSERT INTO delivery_notes ({', '.join(cols)})
VALUES ({', '.join(values)})
ON CONFLICT (delivery_note_id) DO UPDATE SET
    sales_person_id = EXCLUDED.sales_person_id,
    tax_rate_id = EXCLUDED.tax_rate_id,
    quota_amount = EXCLUDED.quota_amount,
    non_quota_amount = EXCLUDED.non_quota_amount,
    tax_amount = EXCLUDED.tax_amount,
    total_amount_ex_tax = EXCLUDED.total_amount_ex_tax,
    total_amount_inc_tax = EXCLUDED.total_amount_inc_tax,
    remarks = EXCLUDED.remarks,
    delivery_note_number = EXCLUDED.delivery_note_number,
    file_path = EXCLUDED.file_path,
    delivery_date = EXCLUDED.delivery_date,
    billing_date = EXCLUDED.billing_date,
    image_filename = EXCLUDED.image_filename,
    deleted_flag = EXCLUDED.deleted_flag,
    updated_at = EXCLUDED.updated_at;
"""
            sqls.append(sql)
    
    return '\n'.join(sqls)

def generate_details_sql():
    """delivery_note_detailsテーブル用のINSERT文を生成"""
    sqls = []
    sqls.append("\n\n-- delivery_note_details テーブルへのデータ投入")
    sqls.append("")
    
    with open(DETAILS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cols = [
                'delivery_note_detail_id',
                'delivery_note_id',
                'product_id',
                'quantity',
                'unit_price',
                'amount',
                'remarks',
                'deleted_flag',
                'created_at',
                'updated_at'
            ]
            
            values = [
                sql_escape(row['delivery_note_detail_id']),
                sql_escape(row['delivery_note_id']),
                sql_escape(row['product_id']),
                sql_escape(row['quantity']),
                sql_escape(row['unit_price']),
                sql_escape(row['amount']),
                sql_escape(row['remarks']),
                sql_escape(row['deleted_flag']),
                sql_escape(row['created_at']),
                sql_escape(row['updated_at'])
            ]
            
            sql = f"""INSERT INTO delivery_note_details ({', '.join(cols)})
VALUES ({', '.join(values)})
ON CONFLICT (delivery_note_detail_id) DO UPDATE SET
    delivery_note_id = EXCLUDED.delivery_note_id,
    product_id = EXCLUDED.product_id,
    quantity = EXCLUDED.quantity,
    unit_price = EXCLUDED.unit_price,
    amount = EXCLUDED.amount,
    remarks = EXCLUDED.remarks,
    deleted_flag = EXCLUDED.deleted_flag,
    updated_at = EXCLUDED.updated_at;
"""
            sqls.append(sql)
    
    return '\n'.join(sqls)

def main():
    print("SQL生成中...")
    
    # SQLファイルを生成
    notes_sql = generate_notes_sql()
    details_sql = generate_details_sql()
    
    full_sql = notes_sql + details_sql
    
    # ファイルに書き込み
    OUTPUT_SQL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_SQL, 'w', encoding='utf-8') as f:
        f.write("-- PostgreSQL INSERT statements for delivery_notes and delivery_note_details\n")
        f.write("-- Generated from CSV files\n\n")
        f.write("BEGIN;\n\n")
        f.write(full_sql)
        f.write("\n\nCOMMIT;\n")
    
    print(f"✓ SQL生成完了: {OUTPUT_SQL}")
    print(f"  - delivery_notes: CSVから読み込み")
    print(f"  - delivery_note_details: CSVから読み込み")
    print(f"\n実行方法:")
    print(f"  psql -U username -d database_name -f {OUTPUT_SQL}")

if __name__ == '__main__':
    main()
