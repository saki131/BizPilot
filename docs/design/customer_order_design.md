# 顧客注文管理 & ゆうちょ入金チェック 設計書

## 1. 概要

顧客からの注文内容を管理し、ゆうちょダイレクトの入金明細CSVと照合して入金状況を確認する機能。
既存の納品書・請求書機能とは独立した機能として実装する。

## 2. データベース設計

### 2.1 customers（顧客マスタ）
```sql
CREATE TABLE customers (
    customer_id    SERIAL PRIMARY KEY,
    name           VARCHAR(200) NOT NULL,     -- 顧客名
    name_kana      VARCHAR(200),              -- 顧客名カナ（振込人名照合用）
    deleted_flag   BOOLEAN DEFAULT FALSE,
    display_order  INTEGER DEFAULT 0,
    created_at     TIMESTAMP DEFAULT NOW(),
    updated_at     TIMESTAMP DEFAULT NOW()
);
```

### 2.2 customer_orders（顧客注文）
```sql
CREATE TABLE customer_orders (
    customer_order_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id        INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date         DATE NOT NULL,                           -- 注文日
    order_amount       INTEGER NOT NULL,                        -- 注文金額
    payment_due_date   DATE NOT NULL,                           -- 入金期限
    payment_status     VARCHAR(20) DEFAULT 'unpaid' NOT NULL,   -- unpaid / paid / overdue
    deposit_record_id  UUID REFERENCES deposit_records(deposit_record_id), -- 紐付き入金記録
    memo               TEXT,                                    -- メモ
    deleted_flag       BOOLEAN DEFAULT FALSE,
    created_at         TIMESTAMP DEFAULT NOW(),
    updated_at         TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_customer_orders_customer ON customer_orders(customer_id);
CREATE INDEX idx_customer_orders_status ON customer_orders(payment_status);
CREATE INDEX idx_customer_orders_due_date ON customer_orders(payment_due_date);
```

### 2.3 deposit_records（入金記録）
```sql
CREATE TABLE deposit_records (
    deposit_record_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deposit_date       DATE NOT NULL,              -- 入金日
    depositor_name     VARCHAR(200),               -- 振込人名（CSV詳細1）
    amount             INTEGER NOT NULL,            -- 入金額
    detail1            VARCHAR(500),               -- CSV詳細1
    detail2            VARCHAR(500),               -- CSV詳細2
    matched_order_id   UUID REFERENCES customer_orders(customer_order_id),  -- 照合済み注文
    upload_batch_id    VARCHAR(100),               -- アップロードバッチID
    created_at         TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_deposit_records_matched ON deposit_records(matched_order_id);
```

## 3. API設計

### 3.1 顧客マスタAPI（既存マスタルーターに追加）
```
GET    /api/masters/customers              顧客一覧
POST   /api/masters/customers              顧客作成
PUT    /api/masters/customers/{id}         顧客更新
DELETE /api/masters/customers/{id}         顧客削除（論理削除）
```

### 3.2 注文API
```
GET    /api/customer-orders/               注文一覧（クエリ: status, customer_id, due_from, due_to）
POST   /api/customer-orders/               注文作成
PUT    /api/customer-orders/{id}           注文更新
DELETE /api/customer-orders/{id}           注文削除（論理削除）
```

### 3.3 入金チェックAPI
```
POST   /api/customer-orders/deposits/upload                      CSVアップロード & 自動照合
GET    /api/customer-orders/deposits/                             入金記録一覧（未照合のみフィルタ可）
POST   /api/customer-orders/deposits/{deposit_id}/match/{order_id}  手動紐付け
DELETE /api/customer-orders/deposits/{deposit_id}/match           紐付け解除
```

## 4. 入金照合ロジック

### 4.1 ゆうちょCSVフォーマット（想定）
```
取引日,摘要,お支払金額,お預り金額,差引残高,メモ
```
※ 実際のCSVカラム名は初回アップロード時にマッピング設定可能にする。

### 4.2 自動照合アルゴリズム
1. CSVの「入金」行（お預り金額 > 0）のみ対象
2. 未入金の注文を取得（payment_status = 'unpaid' or 'overdue'）
3. マッチング条件：
   - **金額一致**: 入金額 = 注文金額
   - **名前照合**: 振込人名 と 顧客名（or 顧客名カナ）の部分一致
4. 照合成功 → 注文の payment_status を 'paid' に更新
5. 照合失敗 → 入金記録は保存し、手動紐付けUIで対応

### 4.3 入金期限チェック
- バックエンドAPI呼び出し時に、未入金かつ `payment_due_date < 今日日付` の注文は `payment_status = 'overdue'` に自動更新

## 5. 画面設計

### 5.1 マスタ管理画面（既存画面に追加）
- 既存タブ「販売員」「商品」「委託先」に **「顧客」タブ** を追加
- 顧客は `名前` と `名前（カナ）` のみ入力

### 5.2 注文管理画面（`/customers` 新規ページ）

#### タブ1: 注文管理
- **注文一覧テーブル**: 顧客名、注文日、注文金額、入金期限、ステータス（色分け）
  - 🟢 入金済（paid） / 🔴 期限超過（overdue） / ⚪ 未入金（unpaid）
- **フィルタ**: ステータス、顧客、期間
- **新規注文フォーム**: 顧客選択（マスタから）、注文金額、入金期限、メモ

#### タブ2: 入金チェック
- **CSVアップロードエリア**: ドラッグ&ドロップ or ファイル選択
- **照合結果表示**: 自動マッチした注文の一覧
- **未照合入金一覧**: 手動で注文と紐付けるUI
- **未入金注文一覧**: 入金待ちの注文

## 6. CSV自動化について

### 6.1 制約事項
- ゆうちょダイレクトは公開APIを提供していない
- CSVダウンロードはゆうちょダイレクトのWeb画面から手動操作が必要
- **CSVダウンロードの自動化は不可**（ブラウザ自動操作はセキュリティ上推奨できない）

### 6.2 本システムで対応する効率化
- CSVアップロード後の照合処理は完全自動化
- 重複アップロード防止（同一バッチの検出）
- 照合結果のワンクリック確認・手動修正
