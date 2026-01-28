import sys
import time
import json
import httpx

# Ensure backend package import works
sys.path.append('.')

from backend.database import SessionLocal
from backend.models import DeliveryNote, DeliveryNoteDetail

API = 'http://localhost:8002/api'
USERNAME = 'admin'
PASSWORD = 'password123'
TEST_IMAGE = 'c:\\Users\\Owner\\workspace\\test_image.jpg'

print('Logging in...')
with httpx.Client() as client:
    login = client.post(f'{API}/auth/login', data={'username': USERNAME, 'password': PASSWORD})
    print('Login status:', login.status_code)
    try:
        token = login.json().get('access_token')
    except Exception as e:
        print('Login response not JSON:', login.text)
        raise

    if not token:
        print('No token returned')
        raise SystemExit(1)

    headers = {'Authorization': f'Bearer {token}'}

    print('Uploading image...')
    with open(TEST_IMAGE, 'rb') as f:
        files = {'file': ('test_image.jpg', f, 'image/jpeg')}
        res = client.post(f'{API}/delivery-notes/recognize-image', headers=headers, files=files, timeout=60)

    print('Upload status:', res.status_code)
    try:
        print('Response JSON:', json.dumps(res.json(), ensure_ascii=False, indent=2))
    except Exception:
        print('Response text:', res.text)

# Small wait to ensure DB commit flushed
time.sleep(1)

# Query DB for latest delivery note
print('\nQuerying DB for latest DeliveryNote...')
session = SessionLocal()
try:
    note = session.query(DeliveryNote).order_by(DeliveryNote.id.desc()).first()
    if not note:
        print('No DeliveryNote found in DB')
    else:
        print('Found DeliveryNote id:', note.id)
        print(' delivery_note_number:', note.delivery_note_number)
        print(' sales_person_id:', note.sales_person_id)
        print(' tax_rate_id:', note.tax_rate_id)
        print(' file_path:', note.file_path)
        print(' image_recognition_data keys:', list((note.image_recognition_data or {}).keys()) if note.image_recognition_data else None)
        details = session.query(DeliveryNoteDetail).filter(DeliveryNoteDetail.delivery_note_id==note.id).all()
        print(' details count:', len(details))
        for d in details:
            print('  - detail id', d.id, 'product_id', d.product_id, 'qty', d.quantity, 'unit', d.unit_price, 'amount', d.amount)
finally:
    session.close()
