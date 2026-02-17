#!/usr/bin/env python3
"""
販売員納品明細CSVから販売員納品書TBLと販売員納品書明細TBLのDB投入用CSVを生成

本番環境のDB構成:
- delivery_notes: delivery_note_id, sales_person_id, tax_rate_id, quota_amount, 
  non_quota_amount, tax_amount, total_amount_ex_tax, total_amount_inc_tax, 
  remarks, delivery_note_number, file_path, delivery_date, billing_date, 
  image_recognition_data, image_filename, deleted_flag, created_at, updated_at

- delivery_note_details: delivery_note_detail_id, delivery_note_id, product_id, 
  quantity, unit_price, amount, remarks, deleted_flag, created_at, updated_at
"""
import csv
import uuid
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 定数
NAMESPACE = uuid.UUID('11111111-1111-1111-1111-111111111111')
INPUT_CSV = Path(__file__).parent / 'sales_delivery_details_input.csv'
NOTES_CSV = Path(__file__).parent.parent / 'sql' / 'delivery_notes.csv'
DETAILS_CSV = Path(__file__).parent.parent / 'sql' / 'delivery_note_details.csv'

UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

def is_uuid(value: str) -> bool:
    """文字列がUUID形式かチェック"""
    return bool(UUID_PATTERN.match(value))

def generate_uuid(old_id: str) -> str:
    """決定論的にUUIDを生成（既にUUIDなら維持）"""
    if is_uuid(old_id):
        return old_id
    return str(uuid.uuid5(NAMESPACE, old_id))

def parse_bool(value: str) -> bool:
    """文字列をbooleanに変換"""
    return value.upper() == 'TRUE'

def parse_int(value: str) -> int:
    """カンマ区切りの数値文字列を整数に変換"""
    return int(value.replace(',', '').strip())

def main():
    # 入力CSVを読み取り
    details_rows = []
    notes_data = defaultdict(lambda: {
        'detail_ids': [],
        'total_amount': 0,
        'deleted_flag': False,
        'non_editable_flag': False
    })
    
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # UUID変換
            detail_id = generate_uuid(row['販売員納品明細ID'])
            note_id = generate_uuid(row['販売員納品ID'])
            
            # 納品書明細データ
            detail = {
                'delivery_note_detail_id': detail_id,
                'delivery_note_id': note_id,
                'product_id': row['品名'],  # 品名は実際は商品IDと想定
                'quantity': parse_int(row['数量']),
                'unit_price': parse_int(row['単価']),
                'amount': parse_int(row['金額（税抜）']),
                'remarks': row['備考'],
                'deleted_flag': parse_bool(row['削除フラグ']),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            details_rows.append(detail)
            
            # 納品書データを集計
            notes_data[note_id]['detail_ids'].append(detail_id)
            notes_data[note_id]['total_amount'] += detail['amount']
            notes_data[note_id]['deleted_flag'] = detail['deleted_flag']
            notes_data[note_id]['non_editable_flag'] = parse_bool(row['編集不可フラグ'])
    
    # 納品書CSVを出力（ヘッダーテーブル）
    NOTES_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(NOTES_CSV, 'w', encoding='utf-8', newline='') as f:
        fieldnames = [
            'delivery_note_id', 'sales_person_id', 'tax_rate_id', 
            'quota_amount', 'non_quota_amount', 'tax_amount', 
            'total_amount_ex_tax', 'total_amount_inc_tax', 'remarks', 
            'delivery_note_number', 'file_path', 'delivery_date', 
            'billing_date', 'image_recognition_data', 'image_filename', 
            'deleted_flag', 'created_at', 'updated_at'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for note_id, note_info in notes_data.items():
            # デフォルト値で納品書レコードを作成
            # 実際の販売員ID、税率ID、日付などは別途設定が必要
            now = datetime.now().isoformat()
            note = {
                'delivery_note_id': note_id,
                'sales_person_id': 1,  # デフォルト販売員ID（要修正）
                'tax_rate_id': 1,  # デフォルト税率ID（要修正）
                'quota_amount': note_info['total_amount'],
                'non_quota_amount': 0,
                'tax_amount': int(note_info['total_amount'] * 0.1),  # 仮で10%
                'total_amount_ex_tax': note_info['total_amount'],
                'total_amount_inc_tax': int(note_info['total_amount'] * 1.1),
                'remarks': '',
                'delivery_note_number': f'DN-{note_id[:8]}',  # 仮の納品書番号
                'file_path': '',
                'delivery_date': now,
                'billing_date': now,
                'image_recognition_data': '',
                'image_filename': '',
                'deleted_flag': note_info['deleted_flag'],
                'created_at': now,
                'updated_at': now
            }
            writer.writerow(note)
    
    print(f"✓ 納品書CSV生成: {NOTES_CSV} ({len(notes_data)} 件)")
    
    # 納品書明細CSVを出力
    with open(DETAILS_CSV, 'w', encoding='utf-8', newline='') as f:
        fieldnames = [
            'delivery_note_detail_id', 'delivery_note_id', 'product_id',
            'quantity', 'unit_price', 'amount', 'remarks',
            'deleted_flag', 'created_at', 'updated_at'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for detail in details_rows:
            writer.writerow(detail)
    
    print(f"✓ 納品書明細CSV生成: {DETAILS_CSV} ({len(details_rows)} 行)")
    print(f"\n⚠️  注意事項:")
    print(f"  - delivery_notes.csv の sales_person_id, tax_rate_id は仮の値（1）です")
    print(f"  - delivery_date, billing_date は現在時刻で設定されています")
    print(f"  - delivery_note_number は仮の番号です")
    print(f"  - 実際のDB投入前に適切な値に修正してください")

if __name__ == '__main__':
    main()
