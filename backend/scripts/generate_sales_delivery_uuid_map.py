#!/usr/bin/env python3
"""
Generate deterministic UUID (v5) mapping for sales delivery IDs.

Inputs (place next to this script or run from repo root):
 - delivery_ids.txt         (one sales_person_delivery_id per line)
 - delivery_details.tsv     (tab-separated: sales_person_delivery_detail_id <TAB> sales_person_delivery_id)

Output:
 - backend/sql/sales_delivery_id_mapping.csv  (old_id,new_uuid)

Behavior:
 - If an old id already matches UUID format, it is kept as-is.
 - Otherwise, a deterministic UUID v5 is generated using a fixed namespace.
"""
from __future__ import annotations
import csv
import os
import re
import sys
import uuid

BASE_DIR = os.path.dirname(__file__)
OUT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'sql'))
OUT_CSV = os.path.join(OUT_DIR, 'sales_delivery_id_mapping.csv')
DELIVERY_IDS_FILE = os.path.join(BASE_DIR, 'delivery_ids.txt')
DETAILS_FILE = os.path.join(BASE_DIR, 'delivery_details.tsv')

# Fixed namespace for deterministic uuid5 generation
NAMESPACE = uuid.UUID('11111111-1111-1111-1111-111111111111')

UUID_RE = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-'
                     r'[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')


def is_uuid(s: str) -> bool:
    if not s:
        return False
    return bool(UUID_RE.match(s.strip()))


def load_ids() -> list[str]:
    ids = []
    # Read delivery_ids.txt if present
    if os.path.exists(DELIVERY_IDS_FILE):
        with open(DELIVERY_IDS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                v = line.strip()
                if v:
                    ids.append(v)

    # Read details file and collect second column values
    if os.path.exists(DETAILS_FILE):
        with open(DETAILS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.rstrip('\n').split('\t')
                if len(parts) >= 2:
                    v = parts[1].strip()
                    if v:
                        ids.append(v)
                else:
                    # Try comma-separated fallback
                    parts2 = line.rstrip('\n').split(',')
                    if len(parts2) >= 2:
                        v = parts2[1].strip()
                        if v:
                            ids.append(v)

    # Unique while preserving order
    seen = set()
    uniq = []
    for v in ids:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


def build_mapping(ids: list[str]) -> dict[str, str]:
    mapping = {}
    for old in ids:
        if is_uuid(old):
            mapping[old] = old
        else:
            # use the textual old id as the 'name' for uuid5
            new = str(uuid.uuid5(NAMESPACE, old))
            mapping[old] = new
    return mapping


def write_csv(mapping: dict[str, str]):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['old_id', 'new_uuid'])
        for old, new in mapping.items():
            writer.writerow([old, new])


def main():
    ids = load_ids()
    if not ids:
        print('No input IDs found. Create', DELIVERY_IDS_FILE, 'and/or', DETAILS_FILE, file=sys.stderr)
        sys.exit(2)

    mapping = build_mapping(ids)
    write_csv(mapping)
    print(f'Wrote {len(mapping)} mappings to {OUT_CSV}')


if __name__ == '__main__':
    main()
