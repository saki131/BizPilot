"""
販売員納品.csvから販売員IDを読み取り、delivery_notes.csvのsales_person_idを更新する
"""
import csv
import uuid

# UUIDマッピングを読み込む
def load_uuid_mapping():
    """sales_delivery_id_mapping.csvからID→UUIDのマッピングを読み込む"""
    mapping = {}
    with open('c:/Users/Owner/workspace/BizPilot/backend/sql/sales_delivery_id_mapping.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row['old_id']] = row['new_uuid']
    return mapping

# 販売員納品IDから販売員IDへのマッピングを作成
def load_sales_person_mapping():
    """sales_delivery_header.csvから販売員納品ID→販売員IDのマッピングを作成"""
    mapping = {}
    with open('c:/Users/Owner/workspace/BizPilot/backend/scripts/sales_delivery_header.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            delivery_id = row['販売員納品ID']
            sales_person_id = row['販売員']
            mapping[delivery_id] = sales_person_id
    print(f"販売員納品IDマッピング: {len(mapping)}件読み込みました")
    return mapping

# delivery_notes.csvを読み込み、sales_person_idを更新
def update_delivery_notes():
    """delivery_notes.csvのsales_person_idを正しい値に更新"""
    uuid_mapping = load_uuid_mapping()
    sales_person_mapping = load_sales_person_mapping()
    
    # delivery_notes.csvを読み込み
    notes = []
    with open('c:/Users/Owner/workspace/BizPilot/backend/sql/delivery_notes.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            notes.append(row)
    
    # 逆引きマッピング: UUID → 元のID
    uuid_to_old_id = {v: k for k, v in uuid_mapping.items()}
    
    # sales_person_idを更新
    updated_count = 0
    for note in notes:
        delivery_note_id = note['delivery_note_id']
        
        # UUIDから元の販売員納品IDを取得
        if delivery_note_id in uuid_to_old_id:
            old_delivery_id = uuid_to_old_id[delivery_note_id]
            
            # 元のIDから販売員IDを取得
            if old_delivery_id in sales_person_mapping:
                new_sales_person_id = sales_person_mapping[old_delivery_id]
                note['sales_person_id'] = new_sales_person_id
                updated_count += 1
            else:
                print(f"警告: 販売員納品ID {old_delivery_id} が販売員マッピングに見つかりません")
        else:
            print(f"警告: UUID {delivery_note_id} が逆引きマッピングに見つかりません")
    
    print(f"{updated_count}件のsales_person_idを更新しました")
    
    # 更新したdelivery_notes.csvを出力
    with open('c:/Users/Owner/workspace/BizPilot/backend/sql/delivery_notes_updated.csv', 'w', encoding='utf-8', newline='') as f:
        # 元のカラム順序を保持
        if notes:
            fieldnames = list(notes[0].keys())
        else:
            fieldnames = ['delivery_note_id', 'sales_person_id', 'tax_rate_id', 'quota_amount', 
                         'non_quota_amount', 'tax_amount', 'total_amount_ex_tax', 'total_amount_inc_tax',
                         'remarks', 'delivery_note_number', 'file_path', 'delivery_date', 'billing_date',
                         'image_recognition_data', 'image_filename', 'deleted_flag', 'created_at', 'updated_at']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(notes)
    
    print("更新されたCSVをdelivery_notes_updated.csvに出力しました")
    
    # 販売員別の集計を表示
    sales_person_counts = {}
    for note in notes:
        sp_id = note['sales_person_id']
        sales_person_counts[sp_id] = sales_person_counts.get(sp_id, 0) + 1
    
    print("\n販売員別の納品書数:")
    for sp_id, count in sorted(sales_person_counts.items(), key=lambda x: int(x[0])):
        print(f"  販売員ID {sp_id}: {count}件")

if __name__ == "__main__":
    update_delivery_notes()
