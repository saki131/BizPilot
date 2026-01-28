# API設計書

## 請求書API仕様

### 1. 一括請求書生成

**エンドポイント**: `POST /api/sales-invoices/bulk-generate`

**説明**: 指定した締め日で、全販売員または特定の販売員の請求書を一括生成します。期間は自動計算されます（前月21日～締め日）。割引率は金額に応じて自動適用されます。

**リクエストボディ**:
```json
{
  "closing_date": "2025-12-20",  // 締め日（必須）
  "sales_person_ids": [1, 2, 3]  // 販売員ID配列（省略時は全販売員）
}
```

**レスポンス**:
```json
{
  "success": true,
  "generated_count": 5,
  "skipped_count": 2,
  "skipped_persons": ["田中太郎", "佐藤花子"],
  "invoices": [...],
  "period": {
    "start_date": "2025-11-21",
    "end_date": "2025-12-20"
  }
}
```

**割引率自動適用ルール**:
- ¥400,000以上: 40%
- ¥200,000以上: 30%
- ¥42,000以上: 20%
- ¥42,000未満: 0%（後で10%に変更可能）

---

### 2. 割引率変更

**エンドポイント**: `PATCH /api/sales-invoices/{invoice_id}/discount-rate`

**説明**: 既存の請求書の割引率を変更し、金額を再計算します。主に0%請求書を10%に変更する用途で使用します。

**リクエストボディ**:
```json
{
  "discount_rate_id": 2  // 新しい割引率ID
}
```

**レスポンス**:
```json
{
  "success": true,
  "message": "Discount rate updated successfully",
  "invoice_id": 123,
  "old_rate": 0.0,
  "new_rate": 0.1,
  "new_total_amount_inc_tax": 99000
}
```

---

### 3. 請求書一覧取得

**エンドポイント**: `GET /api/sales-invoices`

**クエリパラメータ**:
- `sales_person_id`: 販売員IDでフィルタ（省略可）

**レスポンス**:
```json
[
  {
    "id": 1,
    "sales_person_id": 5,
    "sales_person_name": "山田太郎",
    "invoice_number": "T5810180900550",
    "start_date": "2025-11-21",
    "end_date": "2025-12-20",
    "discount_rate_id": 8,
    "discount_rate": 0.0,
    "quota_subtotal": 30000,
    "quota_discount_amount": 0,
    "quota_total": 30000,
    "non_quota_subtotal": 5000,
    "non_quota_discount_amount": 0,
    "non_quota_total": 5000,
    "total_amount_ex_tax": 35000,
    "tax_amount": 3000,
    "total_amount_inc_tax": 38000,
    "details": [
      {
        "id": 1,
        "product_id": 10,
        "product_name": "商品A",
        "total_quantity": 100,
        "unit_price": 300,
        "amount": 30000
      }
    ]
  }
]
```

---

### 4. 請求書詳細取得

**エンドポイント**: `GET /api/sales-invoices/{invoice_id}`

**レスポンス**: 
```json
{
  "id": 1,
  "sales_person_id": 5,
  "sales_person_name": "山田太郎",
  "invoice_number": "T5810180900550",
  "start_date": "2025-11-21",
  "end_date": "2025-12-20",
  "discount_rate_id": 8,
  "discount_rate": 0.0,
  "quota_subtotal": 30000,
  "quota_discount_amount": 0,
  "quota_total": 30000,
  "non_quota_subtotal": 5000,
  "non_quota_discount_amount": 0,
  "non_quota_total": 5000,
  "total_amount_ex_tax": 35000,
  "tax_amount": 3000,
  "total_amount_inc_tax": 38000,
  "details": [
    {
      "id": 1,
      "product_id": 10,
      "product_name": "商品A",
      "total_quantity": 100,
      "unit_price": 300,
      "amount": 30000
    }
  ]
}
```

**レスポンスフィールド**:
- `sales_person_name`: 販売員名（一覧画面で表示用）
- `start_date`, `end_date`: 請求期間（一覧画面で表示用）
- `total_amount_inc_tax`: 税込合計金額（一覧画面で強調表示）
- `details`: 明細配列（明細ダイアログで表示用）

---

### 5. PDF生成

**エンドポイント**: `GET /api/sales-invoices/{invoice_id}/pdf`

**レスポンス**: PDFファイル（application/pdf）

---

## 割引率マスタAPI

### 割引率一覧取得

**エンドポイント**: `GET /api/masters/discount-rates`

**レスポンス**:
```json
[
  {
    "id": 8,
    "rate": "0.00",
    "threshold_amount": 0,
    "customer_flag": true
  },
  {
    "id": 9,
    "rate": "0.10",
    "threshold_amount": 21000,
    "customer_flag": true
  },
  {
    "id": 10,
    "rate": "0.20",
    "threshold_amount": 42000,
    "customer_flag": true
  },
  {
    "id": 11,
    "rate": "0.30",
    "threshold_amount": 200000,
    "customer_flag": true
  },
  {
    "id": 12,
    "rate": "0.40",
    "threshold_amount": 400000,
    "customer_flag": true
  }
]
```

---

## 実装詳細

### 割引率自動計算ロジック

`calculate_optimal_discount_rate(total_amount: int, db: Session) -> DiscountRate`

1. 全割引率を閾値降順で取得
2. 合計金額 >= 閾値 かつ 割引率 > 0% の条件で最初にマッチしたものを返す
3. マッチしなければ0%を返す

### 期間自動計算ロジック

締め日から開始日を計算:
- 締め日が21日以降: 同月21日が開始日
- 締め日が20日以前: 前月21日が開始日

例:
- 締め日: 2025-12-20 → 期間: 2025-11-21 ~ 2025-12-20
- 締め日: 2026-01-20 → 期間: 2025-12-21 ~ 2026-01-20
