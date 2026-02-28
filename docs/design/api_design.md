# API設計書

## 1. API概要
RESTful APIを採用し、JSON形式で通信します。認証はJWTを使用します。

## 2. 共通仕様
- **Base URL**: /api
- **認証**: Bearer Token (JWT)
- **Content-Type**: application/json
- **レスポンス形式**: JSON
- **IDフィールド名視則**:
  - マスタテーブル: INTEGER PK （例: `sales_person_id`, `product_id`）
  - トランザクションテーブル: UUID （例: `delivery_note_id`, `sales_invoice_id`）
- **エラーレスポンス**:
  ```json
  {
    "detail": "error message"
  }
  ```

## 3. エンドポイント詳細

### 認証API
#### POST /api/auth/login
ログイン処理
**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```
**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

#### POST /api/auth/refresh
トークン更新
**Request:**
```json
{
  "refresh_token": "string"
}
```
**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

#### POST /api/auth/logout
ログアウト処理

### マスタAPI
#### GET /api/sales-persons
販売員一覧取得
**Response:**
```json
[
  {
    "sales_person_id": 1,
    "name": "string",
    "deleted_flag": false,
    "display_order": 0,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### POST /api/sales-persons
販売員作成
**Request:**
```json
{
  "name": "string",
  "display_order": 0
}
```

#### GET /api/sales-persons/{sales_person_id}
販売員詳細取得

#### PUT /api/sales-persons/{sales_person_id}
販売員更新

#### DELETE /api/sales-persons/{sales_person_id}
販売員削除（論理削除）

同様のエンドポイントが商品（products）、委託先（contractors）にも存在します。
パスパラメータはそれぞれ `{product_id}`, `{contractor_id}` を使用します。

#### GET /api/discount-rates
割引率一覧取得（読み取りのみ）
**Response:**
```json
[
  {
    "discount_rate_id": 1,
    "rate": "0.20",
    "threshold_amount": 42000,
    "sales_person_flag": true,
    "deleted_flag": false
  }
]
```

#### GET /api/tax-rates
税率一覧取得（読み取りのみ）

### 納品書API
#### POST /api/delivery-notes/recognize-image
画像認識処理
**Request:** multipart/form-data
- image: file (画像ファイル)
- sales_person_id: integer (オプション)

**Response:**
```json
{
  "success": true,
  "data": {
    "sales_person_id": 1,
    "delivery_date": "2024-01-01",
    "details": [
      {
        "product_id": 1,
        "quantity": 10,
        "unit_price": 1000
      }
    ]
  }
}
```

#### GET /api/delivery-notes
納品書一覧取得
**Query Parameters:**
- sales_person_id: integer
- start_date, end_date: date

#### POST /api/delivery-notes
納品書作成
**Request:**
```json
{
  "sales_person_id": 1,
  "tax_rate_id": 1,
  "delivery_date": "2024-01-01",
  "billing_date": "2024-01-20",
  "remarks": "string",
  "details": [
    {
      "product_id": 1,
      "quantity": 10,
      "unit_price": 1000,
      "remarks": "string"
    }
  ]
}
```

#### GET /api/delivery-notes/{delivery_note_id}
納品書詳細取得

#### PUT /api/delivery-notes/{delivery_note_id}
納品書更新

#### DELETE /api/delivery-notes/{delivery_note_id}
納品書削除

#### GET /api/delivery-notes/{delivery_note_id}/pdf
PDF生成・ダウンロード

### 請求書API
#### POST /api/sales-invoices/bulk-generate
販売員請求書一括生成
**Request:**
```json
{
  "closing_date": "2025-12-20",
  "sales_person_ids": [1, 2, 3]
}
```
**Response:**
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

#### PATCH /api/sales-invoices/{sales_invoice_id}/discount-rate
割引率変更および金額再計算
**Request:**
```json
{
  "discount_rate_id": 2
}
```

#### GET /api/sales-invoices
販売員請求書一覧取得
**Query Parameters:**
- sales_person_id: integer (フィルタ, 省略可)

#### GET /api/sales-invoices/{sales_invoice_id}
販売員請求書詳細取得

#### GET /api/sales-invoices/{sales_invoice_id}/pdf
請求書PDF取得

#### GET /api/sales-invoices/{sales_invoice_id}/receipt-pdf
領収書PDF取得

#### PUT /api/sales-invoices/{sales_invoice_id}/receipt-date
領収日更新

#### DELETE /api/sales-invoices/{sales_invoice_id}
請求書削除（論理削除）

委託先請求書も同様のエンドポイントがあります。プレフィックス: `/api/contractor-invoices`、パスパラメータ: `{contractor_invoice_id}`

### 売上統計API

#### GET /api/sales-stats/monthly-totals
月別売上合計一覧取得

全販売員請求書・全委託先請求書の `total_amount_inc_tax`（税込合計）を `invoice_date` の年月で集計します。
削除済み（`deleted_flag=true`）の請求書は除外します。

**Query Parameters:**
- `year`: integer（省略時: サーバー現在年）

**Response:**
```json
[
  {
    "year_month": "2025-01",
    "sales_invoice_total": 1500000,
    "contractor_invoice_total": 800000,
    "grand_total": 2300000
  },
  {
    "year_month": "2025-02",
    "sales_invoice_total": 1200000,
    "contractor_invoice_total": 650000,
    "grand_total": 1850000
  }
]
```

**備考:**
- 請求書が1件もない月のエントリは含まない
- `year_month` は `YYYY-MM` 形式
- 金額はすべて円単位（整数）

---

#### GET /api/sales-stats/monthly-product-quantities
月別商品別数量合計取得

指定した年月の販売員請求書明細・委託先請求書明細の `total_quantity` を商品ごとに集計します。
削除済みの請求書に紐づく明細は除外します。数量0の商品はレスポンスに含みません。

**Query Parameters:**
- `year`: integer（必須）
- `month`: integer（必須, 1〜12）

**Response:**
```json
[
  {
    "product_id": 1,
    "product_name": "商品A",
    "display_order": 1,
    "sales_total_quantity": 120,
    "contractor_total_quantity": 50,
    "grand_total_quantity": 170
  },
  {
    "product_id": 2,
    "product_name": "商品B",
    "display_order": 2,
    "sales_total_quantity": 0,
    "contractor_total_quantity": 30,
    "grand_total_quantity": 30
  }
]
```

**備考:**
- `display_order` 昇順、同値の場合は `product_id` 昇順でソート
- `grand_total_quantity` が0の商品は除外

---

## 4. エラーハンドリング
- 400: Bad Request (バリデーションエラー)
- 401: Unauthorized (認証エラー)
- 403: Forbidden (権限エラー)
- 404: Not Found
- 500: Internal Server Error

## 5. レート制限
- 認証API: 10回/分
- その他API: 100回/分