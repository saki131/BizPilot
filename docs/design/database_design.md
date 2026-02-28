# データベース設計書

## 1. データベース概要
システムは Neon PostgreSQL を使用し、以下の主要テーブルで構成されます。

- **本番/ステージング**: Neon PostgreSQL (ap-southeast-1 リージョン)
- **プライマリキー方針**: マスタテーブルは `SERIAL` (INTEGER)、トランザクションテーブルは `UUID`

## 2. ER図（概略）
```
users (管理者)
 user_id (PK, INTEGER)

sales_persons (販売員)
 sales_person_id (PK, INTEGER)

products (商品)
 product_id (PK, INTEGER)

contractors (委託先)
 contractor_id (PK, INTEGER)

tax_rates (税率)
 tax_rate_id (PK, INTEGER)

discount_rates (割引率)
 discount_rate_id (PK, INTEGER)

delivery_notes (納品書)
 delivery_note_id (PK, UUID)
     delivery_note_details (明細, UUID PK)

sales_invoices (販売員請求書)
 sales_invoice_id (PK, UUID)
     sales_invoice_details (明細, UUID PK)

contractor_invoices (委託先請求書)
 contractor_invoice_id (PK, UUID)
     contractor_invoice_details (明細, UUID PK)
```

## 3. テーブル定義詳細

### users（管理者）
```sql
CREATE TABLE users (
    user_id         SERIAL PRIMARY KEY,
    username        VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    deleted_flag    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

### sales_persons（販売員）
```sql
CREATE TABLE sales_persons (
    sales_person_id SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    deleted_flag    BOOLEAN DEFAULT FALSE,
    display_order   INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

### products（商品）
```sql
CREATE TABLE products (
    product_id              SERIAL PRIMARY KEY,
    name                    VARCHAR(200) NOT NULL,
    price                   INTEGER NOT NULL,           -- 税抜単価
    discount_exclusion_flag BOOLEAN DEFAULT FALSE,      -- 割引対象外フラグ
    quota_exclusion_flag    BOOLEAN DEFAULT FALSE,      -- ノルマ算定除外フラグ
    quota_target_flag       BOOLEAN DEFAULT FALSE,      -- ノルマ対象フラグ
    deleted_flag            BOOLEAN DEFAULT FALSE,
    display_order           INTEGER DEFAULT 0,
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);
```

### contractors（委託先）
```sql
CREATE TABLE contractors (
    contractor_id SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    deleted_flag  BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);
```

### tax_rates（税率）
```sql
CREATE TABLE tax_rates (
    tax_rate_id  SERIAL PRIMARY KEY,
    rate         DECIMAL(4,2) NOT NULL,   -- 例: 0.10 (= 10%)
    display_name VARCHAR(20) NOT NULL,
    deleted_flag BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMP DEFAULT NOW(),
    updated_at   TIMESTAMP DEFAULT NOW()
);
```

### discount_rates（割引率）

> **注意**: `rate` カラムは DB によって小数形式（0.20 = 20%）または整数形式（20 = 20%）で保存されている場合があります。アプリケーション側で `rate >= 1` の場合は 100 で除算する処理を行っています。

```sql
CREATE TABLE discount_rates (
    discount_rate_id  SERIAL PRIMARY KEY,
    rate              DECIMAL(4,2) NOT NULL,   -- 小数 or 整数が混在する可能性あり
    threshold_amount  INTEGER DEFAULT 0,        -- 割引適用下限金額（円）
    sales_person_flag BOOLEAN DEFAULT TRUE,     -- TRUE=販売員向け / FALSE=委託先向け
    deleted_flag      BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);
```

**割引率マスタ（初期データ）**

| rate | threshold_amount | sales_person_flag | 備考 |
|---|---|---|---|
| 0 | 0 | TRUE | 0%（42,000円未満、後で10%に変更可） |
| 10 | 0 | TRUE | 10% |
| 20 | 42000 | TRUE | 20% |
| 30 | 200000 | TRUE | 30% |
| 40 | 400000 | TRUE | 40% |

### delivery_notes（納品書）
```sql
CREATE TABLE delivery_notes (
    delivery_note_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sales_person_id        INTEGER REFERENCES sales_persons(sales_person_id),
    tax_rate_id            INTEGER REFERENCES tax_rates(tax_rate_id),
    quota_amount           INTEGER DEFAULT 0,     -- ノルマ対象合計（税抜）
    non_quota_amount       INTEGER DEFAULT 0,     -- ノルマ対象外合計（税抜）
    tax_amount             INTEGER DEFAULT 0,     -- 消費税額
    total_amount_ex_tax    INTEGER DEFAULT 0,     -- 合計（税抜）
    total_amount_inc_tax   INTEGER DEFAULT 0,     -- 合計（税込）
    remarks                TEXT,
    file_path              VARCHAR(500),
    image_filename         VARCHAR(500),          -- アップロード画像ファイル名
    delivery_date          TIMESTAMP NOT NULL,
    billing_date           TIMESTAMP NOT NULL,
    image_recognition_data JSON,                  -- Gemini APIレスポンス保存用
    deleted_flag           BOOLEAN DEFAULT FALSE,
    created_at             TIMESTAMP DEFAULT NOW(),
    updated_at             TIMESTAMP DEFAULT NOW()
);
```

### delivery_note_details（納品書明細）
```sql
CREATE TABLE delivery_note_details (
    delivery_note_detail_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delivery_note_id        UUID REFERENCES delivery_notes(delivery_note_id) ON DELETE CASCADE,
    product_id              INTEGER REFERENCES products(product_id),
    quantity                INTEGER NOT NULL,
    unit_price              INTEGER NOT NULL,
    amount                  INTEGER NOT NULL,     -- 税抜金額
    remarks                 VARCHAR(200),
    deleted_flag            BOOLEAN DEFAULT FALSE,
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);
```

### sales_invoices（販売員請求書）
```sql
CREATE TABLE sales_invoices (
    sales_invoice_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sales_person_id           INTEGER REFERENCES sales_persons(sales_person_id) NOT NULL,
    tax_rate_id               INTEGER REFERENCES tax_rates(tax_rate_id) NOT NULL,
    discount_rate_id          INTEGER REFERENCES discount_rates(discount_rate_id) NOT NULL,
    invoice_date              DATE,
    receipt_date              DATE,
    note                      VARCHAR(500),           -- 但し書き
    non_discountable_amount   INTEGER DEFAULT 0,      -- 割引対象外金額
    -- ノルマ対象
    quota_subtotal            INTEGER DEFAULT 0,
    quota_discount_amount     INTEGER DEFAULT 0,
    quota_total               INTEGER DEFAULT 0,
    -- ノルマ対象外
    non_quota_subtotal        INTEGER DEFAULT 0,
    non_quota_discount_amount INTEGER DEFAULT 0,
    non_quota_total           INTEGER DEFAULT 0,
    -- 合計
    total_amount_ex_tax       INTEGER DEFAULT 0,
    tax_amount                INTEGER DEFAULT 0,
    total_amount_inc_tax      INTEGER DEFAULT 0,
    deleted_flag              BOOLEAN DEFAULT FALSE,
    created_at                TIMESTAMP DEFAULT NOW(),
    updated_at                TIMESTAMP DEFAULT NOW()
);
```

### sales_invoice_details（販売員請求書明細）
```sql
CREATE TABLE sales_invoice_details (
    sales_invoice_detail_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sales_invoice_id        UUID REFERENCES sales_invoices(sales_invoice_id) ON DELETE CASCADE NOT NULL,
    product_id              INTEGER REFERENCES products(product_id) NOT NULL,
    total_quantity          INTEGER DEFAULT 0,
    unit_price              INTEGER NOT NULL,
    amount                  INTEGER NOT NULL,
    deleted_flag            BOOLEAN DEFAULT FALSE,
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);
```

### contractor_invoices（委託先請求書）
```sql
CREATE TABLE contractor_invoices (
    contractor_invoice_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id             INTEGER REFERENCES contractors(contractor_id) NOT NULL,
    discount_rate_id          INTEGER REFERENCES discount_rates(discount_rate_id) NOT NULL,
    tax_rate_id               INTEGER REFERENCES tax_rates(tax_rate_id) NOT NULL,
    invoice_date              DATE NOT NULL,
    receipt_date              DATE,
    payment_due_date          DATE,
    note                      VARCHAR(500),
    non_discountable_amount   INTEGER DEFAULT 0,
    -- ノルマ対象
    quota_subtotal            INTEGER DEFAULT 0,
    quota_discount_amount     INTEGER DEFAULT 0,
    quota_total               INTEGER DEFAULT 0,
    -- ノルマ対象外
    non_quota_subtotal        INTEGER DEFAULT 0,
    non_quota_discount_amount INTEGER DEFAULT 0,
    non_quota_total           INTEGER DEFAULT 0,
    -- 合計
    total_amount_ex_tax       INTEGER DEFAULT 0,
    total_discount_amount     INTEGER DEFAULT 0,    -- 割引額合計
    total_after_discount      INTEGER DEFAULT 0,    -- 割引後合計
    tax_amount                INTEGER DEFAULT 0,
    total_amount_inc_tax      INTEGER DEFAULT 0,
    deleted_flag              BOOLEAN DEFAULT FALSE,
    created_at                TIMESTAMP DEFAULT NOW(),
    updated_at                TIMESTAMP DEFAULT NOW()
);
```

### contractor_invoice_details（委託先請求書明細）
```sql
CREATE TABLE contractor_invoice_details (
    contractor_invoice_detail_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_invoice_id        UUID REFERENCES contractor_invoices(contractor_invoice_id) ON DELETE CASCADE NOT NULL,
    product_id                   INTEGER REFERENCES products(product_id) NOT NULL,
    total_quantity               INTEGER DEFAULT 0,
    unit_price                   INTEGER NOT NULL,
    amount                       INTEGER NOT NULL,
    deleted_flag                 BOOLEAN DEFAULT FALSE,
    created_at                   TIMESTAMP DEFAULT NOW(),
    updated_at                   TIMESTAMP DEFAULT NOW()
);
```

## 4. インデックス設計
```sql
CREATE INDEX idx_delivery_notes_sales_person    ON delivery_notes(sales_person_id);
CREATE INDEX idx_delivery_notes_date            ON delivery_notes(delivery_date);
CREATE INDEX idx_delivery_note_details_note     ON delivery_note_details(delivery_note_id);
CREATE INDEX idx_sales_invoices_sales_person    ON sales_invoices(sales_person_id);
CREATE INDEX idx_contractor_invoices_contractor ON contractor_invoices(contractor_id);
```

## 5. 論理削除方針
全テーブルに `deleted_flag BOOLEAN DEFAULT FALSE` を持ち、DELETE ではなく論理削除を使用します。
一覧取得 API では `deleted_flag = FALSE` のみを返します。

## 6. 消費税計算の注意事項
`discount_rates.rate` は DB によって以下の2形式で保存される場合があります：
- **小数形式**: `0.10`  10% を意味する
- **整数形式**: `10`  10% を意味する

アプリケーション側（`contractor_invoices.py`, `sales_invoices.py`, `pdf_generator.py`）では `rate >= 1` の場合に 100 で除算する処理で両形式に対応しています。

## 7. マイグレーション
`alembic` を使用してスキーマ管理を行います。
```bash
# マイグレーションファイル生成
alembic revision --autogenerate -m "description"

# マイグレーション実行
alembic upgrade head
```