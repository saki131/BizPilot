#!/usr/bin/env python3
"""
Generate SQL INSERT statements for delivery_notes and delivery_note_details.
Reads from SQL input CSVs and generates INSERT statements with UUID support.
"""
import csv
import os
from datetime import datetime

# Input and output paths
SCRIPT_DIR = os.path.dirname(__file__)
SQL_DIR = os.path.join(SCRIPT_DIR, '..', 'sql')
NOTES_INPUT = os.path.join(SQL_DIR, 'delivery_notes_input.csv')
DETAILS_INPUT = os.path.join(SQL_DIR, 'delivery_note_details_input.csv')
OUTPUT_FILE = os.path.join(SQL_DIR, 'delivery_data_insert.sql')

def clean_value(value):
    """Clean CSV value by removing commas and quotes from numbers"""
    if value is None or value == '':
        return None
    # Remove commas and quotes from numeric values
    cleaned = str(value).replace(',', '').replace('"', '').strip()
    return cleaned if cleaned else None

def format_sql_value(value, field_type='string'):
    """Format value for SQL insertion"""
    if value is None or value == '':
        return 'NULL'
    
    if field_type == 'number':
        # Remove any non-numeric characters except minus and decimal point
        cleaned = clean_value(value)
        if cleaned and cleaned.replace('-', '').replace('.', '').isdigit():
            return cleaned
        return 'NULL'
    elif field_type == 'boolean':
        cleaned = clean_value(value)
        if cleaned and cleaned.upper() in ('TRUE', 'T', '1', 'YES'):
            return 'TRUE'
        elif cleaned and cleaned.upper() in ('FALSE', 'F', '0', 'NO'):
            return 'FALSE'
        return 'FALSE'
    elif field_type == 'date':
        cleaned = clean_value(value)
        if cleaned:
            # Convert YYYY/MM/DD to YYYY-MM-DD
            cleaned = cleaned.replace('/', '-')
            try:
                # Validate date format
                datetime.strptime(cleaned, '%Y-%m-%d')
                return f"'{cleaned}'"
            except ValueError:
                return 'NULL'
        return 'NULL'
    else:  # string
        cleaned = clean_value(value)
        if cleaned:
            # Escape single quotes
            escaped = cleaned.replace("'", "''")
            return f"'{escaped}'"
        return 'NULL'

def generate_notes_insert():
    """Generate INSERT statements for delivery_notes"""
    statements = []
    
    with open(NOTES_INPUT, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            delivery_note_id = clean_value(row.get('delivery_note_id'))
            
            # Skip if no ID
            if not delivery_note_id:
                continue
            
            # Check if UUID format (contains hyphens) or short ID
            if '-' not in delivery_note_id:
                # Short ID - need to generate full UUID
                # Pad with zeros and add UUID format
                delivery_note_id = f"{delivery_note_id}-0000-0000-0000-000000000000"[:36]
            
            cols = []
            vals = []
            
            # Required fields
            cols.append('delivery_note_id')
            vals.append(f"'{delivery_note_id}'::uuid")
            
            # Optional fields
            if row.get('sales_person_id'):
                cols.append('sales_person_id')
                vals.append(format_sql_value(row['sales_person_id'], 'number'))
            
            if row.get('tax_rate_id'):
                cols.append('tax_rate_id')
                vals.append(format_sql_value(row['tax_rate_id'], 'number'))
            
            # Amount fields
            cols.append('quota_amount')
            vals.append(format_sql_value(row.get('quota_amount', '0'), 'number'))
            
            cols.append('non_quota_amount')
            vals.append(format_sql_value(row.get('non_quota_amount', '0'), 'number'))
            
            cols.append('tax_amount')
            vals.append(format_sql_value(row.get('tax_amount', '0'), 'number'))
            
            cols.append('total_amount_ex_tax')
            vals.append(format_sql_value(row.get('total_amount_ex_tax', '0'), 'number'))
            
            cols.append('total_amount_inc_tax')
            vals.append(format_sql_value(row.get('total_amount_inc_tax', '0'), 'number'))
            
            # Text fields
            if row.get('remarks'):
                cols.append('remarks')
                vals.append(format_sql_value(row['remarks'], 'string'))
            
            if row.get('file_path'):
                cols.append('file_path')
                vals.append(format_sql_value(row['file_path'], 'string'))
            
            # Date fields
            cols.append('delivery_date')
            vals.append(format_sql_value(row.get('delivery_date'), 'date'))
            
            cols.append('billing_date')
            vals.append(format_sql_value(row.get('billing_date'), 'date'))
            
            # JSON fields
            if row.get('image_recognition_data'):
                cols.append('image_recognition_data')
                vals.append(format_sql_value(row['image_recognition_data'], 'string'))
            
            if row.get('image_filename'):
                cols.append('image_filename')
                vals.append(format_sql_value(row['image_filename'], 'string'))
            
            # Boolean and timestamp fields
            cols.append('deleted_flag')
            vals.append(format_sql_value(row.get('deleted_flag', 'FALSE'), 'boolean'))
            
            # Generate INSERT statement
            stmt = f"INSERT INTO delivery_notes ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (delivery_note_id) DO NOTHING;"
            statements.append(stmt)
    
    return statements

def generate_details_insert():
    """Generate INSERT statements for delivery_note_details"""
    statements = []
    
    with open(DETAILS_INPUT, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            detail_id = clean_value(row.get('delivery_note_detail_id'))
            note_id = clean_value(row.get('delivery_note_id'))
            
            # Skip if no IDs
            if not detail_id or not note_id:
                continue
            
            # Format IDs as UUIDs
            if '-' not in detail_id:
                detail_id = f"{detail_id}-0000-0000-0000-000000000000"[:36]
            if '-' not in note_id:
                note_id = f"{note_id}-0000-0000-0000-000000000000"[:36]
            
            cols = []
            vals = []
            
            # Required fields
            cols.append('delivery_note_detail_id')
            vals.append(f"'{detail_id}'::uuid")
            
            cols.append('delivery_note_id')
            vals.append(f"'{note_id}'::uuid")
            
            if row.get('product_id'):
                cols.append('product_id')
                vals.append(format_sql_value(row['product_id'], 'number'))
            
            cols.append('quantity')
            vals.append(format_sql_value(row.get('quantity', '0'), 'number'))
            
            cols.append('unit_price')
            vals.append(format_sql_value(row.get('unit_price', '0'), 'number'))
            
            cols.append('amount')
            vals.append(format_sql_value(row.get('amount', '0'), 'number'))
            
            # Optional fields
            if row.get('remarks'):
                cols.append('remarks')
                vals.append(format_sql_value(row['remarks'], 'string'))
            
            cols.append('deleted_flag')
            vals.append(format_sql_value(row.get('deleted_flag', 'FALSE'), 'boolean'))
            
            # Generate INSERT statement
            stmt = f"INSERT INTO delivery_note_details ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (delivery_note_detail_id) DO NOTHING;"
            statements.append(stmt)
    
    return statements

def main():
    """Main execution"""
    print("Generating SQL INSERT statements...")
    
    # Generate statements
    notes_statements = generate_notes_insert()
    details_statements = generate_details_insert()
    
    print(f"Generated {len(notes_statements)} delivery_notes INSERT statements")
    print(f"Generated {len(details_statements)} delivery_note_details INSERT statements")
    
    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("-- Generated SQL INSERT statements for delivery_notes and delivery_note_details\n")
        f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("BEGIN;\n\n")
        
        f.write("-- delivery_notes\n")
        for stmt in notes_statements:
            f.write(stmt + "\n")
        
        f.write("\n-- delivery_note_details\n")
        for stmt in details_statements:
            f.write(stmt + "\n")
        
        f.write("\nCOMMIT;\n")
    
    print(f"\nSQL file written to: {OUTPUT_FILE}")
    print("You can execute this file with: psql -f backend/sql/delivery_data_insert.sql")

if __name__ == '__main__':
    main()
