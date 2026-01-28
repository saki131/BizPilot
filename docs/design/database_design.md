# データベース設計書

## 1. データベース概要
システムはPostgreSQL 15を使用し、以下の主要テーブルで構成されます。

## 2. ER図
```
users (管理者)
├── id (PK)
├── username
├── hashed_password
├── created_at
└── updated_at

sales_persons (販売員)
├── id (PK)
├── name
├── deleted_flag
├── created_at
└── updated_at

products (商品)
├── id (PK)
├── name
├── price
├── discount_exclusion_flag
├── quota_exclusion_flag
├── quota_target_flag
├── deleted_flag
├── display_order
├── created_at
└── updated_at

contractors (委託先)
├── id (PK)
├── name
├── deleted_flag
├── created_at
└── updated_at

tax_rates (税率)
├── id (PK)
├── rate
├── display_name
├── deleted_flag
├── created_at
└── updated_at

discount_rates (割引率)
├── id (PK)
├── rate
├── customer_flag
├── deleted_flag
├── created_at
└── updated_at

delivery_notes (納品書)
├── id (PK)
├── sales_person_id (FK)
├── tax_rate_id (FK)
├── quota_amount
├── non_quota_amount
├── tax_amount
├── total_amount_ex_tax
├── total_amount_inc_tax
├── remarks
├── delivery_note_number
├── file_path
├── delivery_date
├── billing_date
├── image_recognition_data (JSONB)
├── created_at
└── updated_at

delivery_note_details (納品書明細)
├── id (PK)
├── delivery_note_id (FK)
├── product_id (FK)
├── quantity
├── unit_price
├── amount
├── remarks
├── created_at
└── updated_at

sales_invoices (販売員請求書)
contractor_invoices (委託先請求書)
(詳細は省略)
```

## 3. テーブル定義詳細

### users（管理者）
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### sales_persons（販売員）
```sql
CREATE TABLE sales_persons (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    deleted_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### products（商品）
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price INTEGER NOT NULL,
    discount_exclusion_flag BOOLEAN DEFAULT FALSE,
    quota_exclusion_flag BOOLEAN DEFAULT FALSE,
    quota_target_flag BOOLEAN DEFAULT FALSE,
    deleted_flag BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### contractors（委託先）
```sql
CREATE TABLE contractors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    deleted_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### tax_rates（税率）
```sql
CREATE TABLE tax_rates (
    id SERIAL PRIMARY KEY,
    rate DECIMAL(4,2) NOT NULL,
    display_name VARCHAR(20) NOT NULL,
    deleted_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### discount_rates（割引率）
```sql
CREATE TABLE discount_rates (
    id SERIAL PRIMARY KEY,
    rate DECIMAL(4,2) NOT NULL,
    customer_flag BOOLEAN DEFAULT TRUE,
    deleted_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### delivery_notes（納品書）
```sql
CREATE TABLE delivery_notes (
    id SERIAL PRIMARY KEY,
    sales_person_id INTEGER REFERENCES sales_persons(id),
    tax_rate_id INTEGER REFERENCES tax_rates(id),
    quota_amount INTEGER DEFAULT 0,
    non_quota_amount INTEGER DEFAULT 0,
    tax_amount INTEGER DEFAULT 0,
    total_amount_ex_tax INTEGER DEFAULT 0,
    total_amount_inc_tax INTEGER DEFAULT 0,
    remarks TEXT,
    delivery_note_number VARCHAR(50) UNIQUE NOT NULL,
    file_path VARCHAR(500),
    delivery_date DATE NOT NULL,
    billing_date DATE NOT NULL,
    image_recognition_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### delivery_note_details（納品書明細）
```sql
CREATE TABLE delivery_note_details (
    id SERIAL PRIMARY KEY,
    delivery_note_id INTEGER REFERENCES delivery_notes(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    remarks VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 4. インデックス設計
```sql
CREATE INDEX idx_delivery_notes_sales_person ON delivery_notes(sales_person_id);
CREATE INDEX idx_delivery_notes_date ON delivery_notes(delivery_date);
CREATE INDEX idx_delivery_note_details_delivery_note ON delivery_note_details(delivery_note_id);
```

## 5. 制約とトリガー
- 外部キー制約: 参照整合性を確保
- UNIQUE制約: delivery_note_number の一意性
- CHECK制約: 金額フィールドの非負数チェック
- トリガー: updated_at の自動更新