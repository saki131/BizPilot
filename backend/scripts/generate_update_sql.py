"""
更新されたdelivery_notes_updated.csvからUPDATE文を生成する
"""
import csv

def generate_update_sql():
    """delivery_notes_updated.csvからUPDATE SQL文を生成"""
    
    sql_statements = []
    
    with open('c:/Users/Owner/workspace/BizPilot/backend/sql/delivery_notes_updated.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            delivery_note_id = row['delivery_note_id']
            sales_person_id = row['sales_person_id']
            
            sql = f"""UPDATE delivery_notes 
SET sales_person_id = {sales_person_id}
WHERE delivery_note_id = '{delivery_note_id}';"""
            
            sql_statements.append(sql)
    
    # SQLファイルに出力
    with open('c:/Users/Owner/workspace/BizPilot/backend/sql/update_sales_person_ids.sql', 'w', encoding='utf-8') as f:
        f.write("-- 販売員IDを更新するSQL\n")
        f.write("BEGIN;\n\n")
        f.write("\n\n".join(sql_statements))
        f.write("\n\nCOMMIT;\n")
    
    print(f"{len(sql_statements)}件のUPDATE文を生成しました")
    print("出力ファイル: update_sales_person_ids.sql")

if __name__ == "__main__":
    generate_update_sql()
