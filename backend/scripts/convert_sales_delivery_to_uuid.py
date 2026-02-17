#!/usr/bin/env python3
"""
販売員納品明細CSVから全IDを抽出してUUIDに変換し、DB投入用CSVを生成
"""
import csv
import uuid
import re
from pathlib import Path

# 定数
NAMESPACE = uuid.UUID('11111111-1111-1111-1111-111111111111')
INPUT_CSV = Path(__file__).parent / 'sales_delivery_details_input.csv'
OUTPUT_CSV = Path(__file__).parent.parent / 'sql' / 'sales_delivery_details_output.csv'
MAPPING_CSV = Path(__file__).parent.parent / 'sql' / 'sales_delivery_id_mapping.csv'

UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

def is_uuid(value: str) -> bool:
    """文字列がUUID形式かチェック"""
    return bool(UUID_PATTERN.match(value))

def generate_uuid(old_id: str) -> str:
    """決定論的にUUIDを生成（既にUUIDなら維持）"""
    if is_uuid(old_id):
        return old_id
    return str(uuid.uuid5(NAMESPACE, old_id))

def main():
    # 入力CSVを読み取り
    rows = []
    all_ids = set()
    
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            # 4種類のID列を収集
            all_ids.add(row['販売員納品明細ID'])
            all_ids.add(row['販売員納品ID'])
            if row['販売員請求書鏡ID']:
                all_ids.add(row['販売員請求書鏡ID'])
            if row['販売員請求書鏡明細ID']:
                all_ids.add(row['販売員請求書鏡明細ID'])
    
    # IDマッピングを生成
    id_mapping = {old: generate_uuid(old) for old in all_ids}
    
    # マッピングCSVを出力
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(MAPPING_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['old_id', 'new_uuid'])
        for old_id in sorted(id_mapping.keys()):
            writer.writerow([old_id, id_mapping[old_id]])
    
    print(f"✓ マッピングCSV生成: {MAPPING_CSV} ({len(id_mapping)} 件)")
    
    # DB投入用CSVを生成（全IDをUUIDに変換）
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        fieldnames = [
            '販売員納品明細ID', '販売員納品ID', '品名', '数量', '単価', 
            '金額（税抜）', '備考', '販売員請求書鏡ID', '販売員請求書鏡明細ID',
            '削除フラグ', '編集不可フラグ', '未反映数'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in rows:
            converted_row = row.copy()
            converted_row['販売員納品明細ID'] = id_mapping[row['販売員納品明細ID']]
            converted_row['販売員納品ID'] = id_mapping[row['販売員納品ID']]
            if row['販売員請求書鏡ID']:
                converted_row['販売員請求書鏡ID'] = id_mapping[row['販売員請求書鏡ID']]
            if row['販売員請求書鏡明細ID']:
                converted_row['販売員請求書鏡明細ID'] = id_mapping[row['販売員請求書鏡明細ID']]
            writer.writerow(converted_row)
    
    print(f"✓ DB投入用CSV生成: {OUTPUT_CSV} ({len(rows)} 行)")
    print(f"\n変換統計:")
    print(f"  - ユニークID数: {len(id_mapping)}")
    print(f"  - データ行数: {len(rows)}")

if __name__ == '__main__':
    main()
