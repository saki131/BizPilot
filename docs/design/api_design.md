# API設計書

## 1. API概要
RESTful APIを採用し、JSON形式で通信します。認証はJWTを使用します。

## 2. 共通仕様
- **Base URL**: /api
- **認証**: Bearer Token (JWT)
- **Content-Type**: application/json
- **レスポンス形式**: JSON
- **エラーレスポンス**:
  ```json
  {
    "error": "error_code",
    "message": "error message"
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
**Query Parameters:**
- page: integer (default: 1)
- limit: integer (default: 10)
- search: string
- sort: string (name, created_at)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "string",
      "deleted_flag": false,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 32,
  "page": 1,
  "limit": 10
}
```

#### POST /api/sales-persons
販売員作成
**Request:**
```json
{
  "name": "string"
}
```

#### GET /api/sales-persons/{id}
販売員詳細取得

#### PUT /api/sales-persons/{id}
販売員更新
**Request:**
```json
{
  "name": "string"
}
```

#### DELETE /api/sales-persons/{id}
販売員削除（論理削除）

同様のエンドポイントが商品(products)、委託先(contractors)、税率(tax-rates)、割引率(discount-rates)にも存在します。

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
    "delivery_date": "2023-01-01",
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
- page, limit, search, sort
- sales_person_id: integer
- start_date, end_date: date

#### POST /api/delivery-notes
納品書作成
**Request:**
```json
{
  "sales_person_id": 1,
  "tax_rate_id": 1,
  "delivery_date": "2023-01-01",
  "billing_date": "2023-01-01",
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

#### GET /api/delivery-notes/{id}
納品書詳細取得

#### PUT /api/delivery-notes/{id}
納品書更新

#### DELETE /api/delivery-notes/{id}
納品書削除

#### GET /api/delivery-notes/{id}/pdf
PDF生成・ダウンロード

### 請求書API
#### POST /api/sales-invoices/generate
販売員請求書生成
**Request:**
```json
{
  "sales_person_id": 1,
  "start_date": "2023-01-01",
  "end_date": "2023-01-31",
  "discount_rate_id": 1
}
```

#### GET /api/sales-invoices
販売員請求書一覧取得

#### GET /api/sales-invoices/{id}/pdf
PDF取得

委託先請求書も同様のエンドポイントがあります。

## 4. エラーハンドリング
- 400: Bad Request (バリデーションエラー)
- 401: Unauthorized (認証エラー)
- 403: Forbidden (権限エラー)
- 404: Not Found
- 500: Internal Server Error

## 5. レート制限
- 認証API: 10回/分
- その他API: 100回/分