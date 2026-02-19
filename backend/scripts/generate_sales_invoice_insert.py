#!/usr/bin/env python3
"""
Generate SQL INSERT statements for sales_invoices and sales_invoice_details.
Reads from SQL input CSVs and generates INSERT statements with UUID support.
"""
import csv
import os
from datetime import datetime

# Input and output paths
SCRIPT_DIR = os.path.dirname(__file__)
SQL_DIR = os.path.join(SCRIPT_DIR, '..', 'sql')
INVOICES_INPUT = os.path.join(SQL_DIR, 'sales_invoices_input.csv')
DETAILS_INPUT = os.path.join(SQL_DIR, 'sales_invoice_details_input.csv')
OUTPUT_FILE = os.path.join(SQL_DIR, 'sales_invoice_insert.sql')

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

def generate_invoices_insert():
    """Generate INSERT statements for sales_invoices"""
    statements = []
    
    with open(INVOICES_INPUT, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            invoice_id = clean_value(row.get('sales_invoice_id'))
            
            # Skip if no ID
            if not invoice_id:
                continue
            
            # Skip deleted records
            deleted_flag = clean_value(row.get('deleted_flag', 'FALSE'))
            if deleted_flag and deleted_flag.upper() in ('TRUE', 'T', '1', 'YES'):
                continue
            
            # Check if UUID format (contains hyphens) or short ID
            if '-' not in invoice_id:
                # Short ID - need to generate full UUID
                invoice_id = f"{invoice_id}-0000-0000-0000-000000000000"[:36]
            
            cols = []
            vals = []
            
            # Required fields
            cols.append('sales_invoice_id')
            vals.append(f"'{invoice_id}'::uuid")
            
            # Foreign keys
            if row.get('sales_person_id'):
                cols.append('sales_person_id')
                vals.append(format_sql_value(row['sales_person_id'], 'number'))
            
            if row.get('tax_rate_id'):
                cols.append('tax_rate_id')
                vals.append(format_sql_value(row['tax_rate_id'], 'number'))
            
            if row.get('discount_rate_id'):
                cols.append('discount_rate_id')
                vals.append(format_sql_value(row['discount_rate_id'], 'number'))
            
            # Date fields
            if row.get('invoice_date'):
                cols.append('invoice_date')
                vals.append(format_sql_value(row['invoice_date'], 'date'))
            
            # Always include receipt_date even if empty
            cols.append('receipt_date')
            vals.append(format_sql_value(row.get('receipt_date', ''), 'date'))
            
            # Amount fields
            cols.append('non_discountable_amount')
            vals.append(format_sql_value(row.get('non_discountable_amount', '0'), 'number'))
            
            # Always include note even if empty
            cols.append('note')
            vals.append(format_sql_value(row.get('note', ''), 'string'))
            
            # Quota amounts
            cols.append('quota_subtotal')
            vals.append(format_sql_value(row.get('quota_subtotal', '0'), 'number'))
            
            cols.append('quota_discount_amount')
            vals.append(format_sql_value(row.get('quota_discount_amount', '0'), 'number'))
            
            cols.append('quota_total')
            vals.append(format_sql_value(row.get('quota_total', '0'), 'number'))
            
            # Non-quota amounts
            cols.append('non_quota_subtotal')
            vals.append(format_sql_value(row.get('non_quota_subtotal', '0'), 'number'))
            
            cols.append('non_quota_discount_amount')
            vals.append(format_sql_value(row.get('non_quota_discount_amount', '0'), 'number'))
            
            cols.append('non_quota_total')
            vals.append(format_sql_value(row.get('non_quota_total', '0'), 'number'))
            
            # Total amounts
            cols.append('total_amount_ex_tax')
            vals.append(format_sql_value(row.get('total_amount_ex_tax', '0'), 'number'))
            
            cols.append('tax_amount')
            vals.append(format_sql_value(row.get('tax_amount', '0'), 'number'))
            
            cols.append('total_amount_inc_tax')
            vals.append(format_sql_value(row.get('total_amount_inc_tax', '0'), 'number'))
            
            # Boolean field
            cols.append('deleted_flag')
            vals.append(format_sql_value(row.get('deleted_flag', 'FALSE'), 'boolean'))
            
            # Generate INSERT statement
            stmt = f"INSERT INTO sales_invoices ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (sales_invoice_id) DO NOTHING;"
            statements.append(stmt)
    
    return statements

def generate_details_insert():
    """Generate INSERT statements for sales_invoice_details"""
    statements = []
    
    with open(DETAILS_INPUT, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            detail_id = clean_value(row.get('sales_invoice_detail_id'))
            invoice_id = clean_value(row.get('sales_invoice_id'))
            
            # Skip if no IDs
            if not detail_id or not invoice_id:
                continue
            
            # Skip deleted records
            deleted_flag = clean_value(row.get('deleted_flag', 'FALSE'))
            if deleted_flag and deleted_flag.upper() in ('TRUE', 'T', '1', 'YES'):
                continue
            
            # Format IDs as UUIDs
            if '-' not in detail_id:
                detail_id = f"{detail_id}-0000-0000-0000-000000000000"[:36]
            if '-' not in invoice_id:
                invoice_id = f"{invoice_id}-0000-0000-0000-000000000000"[:36]
            
            cols = []
            vals = []
            
            # Required fields
            cols.append('sales_invoice_detail_id')
            vals.append(f"'{detail_id}'::uuid")
            
            cols.append('sales_invoice_id')
            vals.append(f"'{invoice_id}'::uuid")
            
            if row.get('product_id'):
                cols.append('product_id')
                vals.append(format_sql_value(row['product_id'], 'number'))
            
            cols.append('total_quantity')
            vals.append(format_sql_value(row.get('total_quantity', '0'), 'number'))
            
            cols.append('unit_price')
            vals.append(format_sql_value(row.get('unit_price', '0'), 'number'))
            
            cols.append('amount')
            vals.append(format_sql_value(row.get('amount', '0'), 'number'))
            
            cols.append('deleted_flag')
            vals.append(format_sql_value(row.get('deleted_flag', 'FALSE'), 'boolean'))
            
            # Generate INSERT statement
            stmt = f"INSERT INTO sales_invoice_details ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (sales_invoice_detail_id) DO NOTHING;"
            statements.append(stmt)
    
    return statements

def main():
    """Main execution"""
    print("Generating SQL INSERT statements for sales invoices...")
    
    # Generate statements
    invoices_statements = generate_invoices_insert()
    details_statements = generate_details_insert()
    
    print(f"Generated {len(invoices_statements)} sales_invoices INSERT statements")
    print(f"Generated {len(details_statements)} sales_invoice_details INSERT statements")
    
    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("-- Generated SQL INSERT statements for sales_invoices and sales_invoice_details\n")
        f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("BEGIN;\n\n")
        
        f.write("-- sales_invoices\n")
        for stmt in invoices_statements:
            f.write(stmt + "\n")
        
        f.write("\n-- sales_invoice_details\n")
        for stmt in details_statements:
            f.write(stmt + "\n")
        
        f.write("\nCOMMIT;\n")
    
    print(f"\nSQL file written to: {OUTPUT_FILE}")
    print("You can execute this file with: psql -f backend/sql/sales_invoice_insert.sql")

if __name__ == '__main__':
    main()
