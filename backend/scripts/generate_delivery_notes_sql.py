#!/usr/bin/env python3
"""
Generate SQL INSERT ... ON CONFLICT statements for delivery_notes.

Usage:
 - Paste your raw tab/CSV rows into the RAW variable below, or
 - Pipe/tab the data into the script via stdin (recommended for large datasets):
     cat data.tsv | python backend/scripts/generate_delivery_notes_sql.py

The script writes `backend/sql/delivery_notes_import.sql` by default.
"""
from __future__ import annotations
import csv
import os
import sys
import io
from datetime import datetime

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'sql')
OUT_FILE = os.path.normpath(os.path.join(OUT_DIR, 'delivery_notes_import.sql'))

# If you prefer to paste data directly, put it here as a triple-quoted string.
# Expecting tab or comma separated rows with a header row. Example header names
# should include: delivery_note_number, delivery_date, billing_date, sales_person_id,
# quota_amount, non_quota_amount, tax_amount, total_amount_ex_tax,
# total_amount_inc_tax, remarks, file_path, tax_rate_id, deleted_flag
RAW = """"
"""

def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)

def parse_bool(v: str):
    if v is None:
        return None
    v = v.strip().lower()
    if v in ('1', 'true', 't', 'yes', 'y'):
        return True
    if v in ('0', 'false', 'f', 'no', 'n'):
        return False
    return None

def normalize_number(v: str):
    if v is None:
        return None
    s = v.strip()
    if s == '':
        return None
    # remove commas and any non-digit except minus
    allowed = set('0123456789-')
    return ''.join(ch for ch in s if ch in allowed)

def normalize_date(v: str):
    if v is None:
        return None
    s = v.strip()
    if s == '':
        return None
    # Try common formats
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S'):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            continue
    # fallback: return raw escaped
    return s

def sql_escape(s: str):
    if s is None:
        return 'NULL'
    t = str(s)
    if t == '':
        return 'NULL'
    return "'" + t.replace("'", "''") + "'"

def build_insert(row: dict):
    # Map input keys to DB columns expected by backend.models.DeliveryNote
    # Required: delivery_note_number
    dn = row.get('delivery_note_number') or row.get('delivery_note_no') or row.get('no')
    if not dn:
        return None

    delivery_note_number = dn.strip()
    delivery_date = normalize_date(row.get('delivery_date'))
    billing_date = normalize_date(row.get('billing_date'))
    sales_person_id = normalize_number(row.get('sales_person_id') or row.get('sales_person'))
    tax_rate_id = normalize_number(row.get('tax_rate_id') or row.get('tax_rate'))
    quota_amount = normalize_number(row.get('quota_amount'))
    non_quota_amount = normalize_number(row.get('non_quota_amount'))
    tax_amount = normalize_number(row.get('tax_amount'))
    total_amount_ex_tax = normalize_number(row.get('total_amount_ex_tax') or row.get('total_ex'))
    total_amount_inc_tax = normalize_number(row.get('total_amount_inc_tax') or row.get('total_inc'))
    remarks = row.get('remarks')
    file_path = row.get('file_path')
    deleted_flag = parse_bool(row.get('deleted_flag'))

    cols = []
    vals = []
    upds = []

    def add(col, val_sql, upd=True):
        cols.append(col)
        vals.append(val_sql)
        if upd:
            upds.append(f"{col} = EXCLUDED.{col}")

    add('delivery_note_number', sql_escape(delivery_note_number), upd=False)

    if delivery_date:
        add('delivery_date', f"'{delivery_date}'")
    else:
        add('delivery_date', 'NULL')

    if billing_date:
        add('billing_date', f"'{billing_date}'")
    else:
        add('billing_date', 'NULL')

    if sales_person_id:
        add('sales_person_id', sales_person_id)
    if tax_rate_id:
        add('tax_rate_id', tax_rate_id)
    add('quota_amount', quota_amount or '0')
    add('non_quota_amount', non_quota_amount or '0')
    add('tax_amount', tax_amount or '0')
    add('total_amount_ex_tax', total_amount_ex_tax or '0')
    add('total_amount_inc_tax', total_amount_inc_tax or '0')

    add('remarks', sql_escape(remarks))
    add('file_path', sql_escape(file_path))

    if deleted_flag is not None:
        add('deleted_flag', 'TRUE' if deleted_flag else 'FALSE')

    cols_sql = ', '.join(cols)
    vals_sql = ', '.join(vals)
    upds_sql = ', '.join(upds) if upds else ''

    if upds_sql:
        stmt = f"INSERT INTO delivery_notes ({cols_sql}) VALUES ({vals_sql}) ON CONFLICT (delivery_note_number) DO UPDATE SET {upds_sql};"
    else:
        stmt = f"INSERT INTO delivery_notes ({cols_sql}) VALUES ({vals_sql}) ON CONFLICT (delivery_note_number) DO NOTHING;"
    return stmt

def read_input_rows():
    # Prefer RAW if provided, else read stdin
    if RAW.strip():
        stream = io.StringIO(RAW)
    else:
        if sys.stdin.isatty():
            print('No RAW data provided and no stdin input detected. Please provide data.', file=sys.stderr)
            sys.exit(2)
        stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

    sample = stream.read()
    # Try to detect delimiter: tab or comma
    if '\t' in sample:
        delim = '\t'
    else:
        delim = ','
    stream = io.StringIO(sample)
    reader = csv.DictReader(stream, delimiter=delim)
    for r in reader:
        yield {k.strip(): (v if v is not None else '') for k, v in r.items()}

def main():
    ensure_out_dir()
    stmts = []
    for row in read_input_rows():
        stmt = build_insert(row)
        if stmt:
            stmts.append(stmt)

    if not stmts:
        print('No valid rows parsed; no SQL generated.', file=sys.stderr)
        sys.exit(1)

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        f.write('-- Generated by backend/scripts/generate_delivery_notes_sql.py\n')
        f.write('BEGIN;\n')
        for s in stmts:
            f.write(s + "\n")
        f.write('COMMIT;\n')

    print(f'Wrote SQL to {OUT_FILE}')

if __name__ == '__main__':
    main()
