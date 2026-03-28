# 顧客注文管理 & ゆうちょ入金履歴 設計書

## 1. 概要

顧客からの注文内容を管理し、ゆうちょダイレクトの入金明細CSVから入金記録を取り込む機能。
CSV取り込み時に注文との自動照合を行い、一致する注文のステータスを更新する。
注文台帳の画像からの一括登録機能も提供する。
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
    order_date         DATE NOT NULL,                           -- 登録日（旧: 注文日）
    order_amount       INTEGER NOT NULL,                        -- 注文金額
    payment_due_date   DATE NOT NULL,                           -- 入金期限（登録日+10日で自動設定）
    payment_status     VARCHAR(20) DEFAULT 'unpaid' NOT NULL,   -- unpaid / paid
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
    deposit_date       DATE NOT NULL,              -- 入金日（取引日）
    transaction_id     VARCHAR(100),               -- 入出金取引番号
    depositor_name     VARCHAR(200),               -- 振込人名（CSV詳細2）
    amount             INTEGER NOT NULL,            -- 入金額
    detail1            VARCHAR(500),               -- CSV詳細1（入金/振込等の区分）
    detail2            VARCHAR(500),               -- CSV詳細2（振込人名）
    balance            INTEGER,                    -- 残高
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
POST   /api/customer-orders/               注文作成（登録日=当日、入金期限=登録日+10日を自動設定）
POST   /api/customer-orders/bulk           注文一括作成（画像認識結果から複数注文を一括登録）
POST   /api/customer-orders/recognize-image 注文台帳画像認識（Gemini APIで画像から注文情報を読み取り）
PUT    /api/customer-orders/{id}           注文更新
DELETE /api/customer-orders/{id}           注文削除（論理削除）
```

### 3.3 入金履歴API
```
POST   /api/customer-orders/deposits/upload          CSVアップロード & 自動照合（照合結果を返却）
POST   /api/customer-orders/deposits/confirm-match   部分一致確認後のステータス更新
GET    /api/customer-orders/deposits/                 入金記録一覧（照合結果なし、CSV取り込み分のみ）
```

## 4. 入金照合ロジック

### 4.1 ゆうちょCSVフォーマット（残高等通知明細）
```
ヘッダー行（3行）:
  残高等通知明細残高合計:XXXXX,円,
  出力日時:令和 XX 年 XX 月 XX 日 XX 時 XX 分
  残高等通知明細番号:XXXXX
  対象:番号指定
  日付指定:令和 XX 年 XX 月 XX 日 ～ 令和 XX 年 XX 月 XX 日
  明細件数:XX
データ行:
  取引日,入出金取引番号,お預り金額(円),お支払金額(円),詳細1,詳細2,残高(残付)額,
```
- 取引日: YYYYMMDD形式
- 入出金取引番号: YYYYMMDDnnnnnnn形式
- お預り金額(円): 入金額（空の場合は出金行）
- お支払金額(円): 出金額
- 詳細1: 入金/振込等の区分
- 詳細2: 振込人名（照合対象）
- 残高(残付)額: 残高

### 4.2 自動照合アルゴリズム
1. CSVヘッダー行（先頭3行）をスキップ
2. 入金行（お預り金額 > 0）のみ対象
3. 未入金の注文を取得（payment_status = 'unpaid'）
4. マッチング条件（すべて満たす場合に照合成功）:
   - **金額一致**: 入金額 = 注文金額
   - **名前照合**: 振込人名と顧客名（or 顧客名カナ）の照合
     - 完全一致: 自動でステータス更新
     - 部分一致（漢字↔カタカナ等）: 「候補一致」としてフロントに返却し確認を促す
   - **日付範囲**: 入金日が注文の登録日 ≤ 入金日 ≤ 入金期限の範囲内
5. 完全一致 → 注文の payment_status を 'paid' に更新、deposit_record_idを紐付け
6. 部分一致 → レスポンスに「要確認」として返却、フロントで確認後にconfirm-matchで更新

### 4.3 入金期限
- 注文作成時に自動設定: 登録日 + 10日
- 入金期限超過かつ未入金の注文行はフロントエンドで赤色表示
- overdueステータスは廃止（unpaid/paidの2ステータスのみ）

## 5. 画面設計

### 5.1 マスタ管理画面（既存画面に追加）
- 既存タブ「販売員」「商品」「委託先」に **「顧客」タブ** を追加
- 顧客は `名前` と `名前（カナ）` のみ入力

### 5.2 注文管理画面（`/customers` 新規ページ）

#### タブ1: 注文管理
- **注文一覧テーブル**: 顧客名、登録日、注文金額、入金期限、ステータス（色分け）
  - 🟢 入金済（paid） / ⚪ 未入金（unpaid）
  - 入金期限超過かつ未入金の行は赤背景で強調表示
- **フィルタ**: ステータス、顧客、期間
- **新規注文フォーム**: 顧客選択（マスタから）、注文金額、メモ
  - 登録日は当日日付を自動設定
  - 入金期限は登録日+10日を自動設定
- **画像一括登録**: 注文台帳画像をアップロード → Gemini APIで読み取り → 確認 → 一括登録

#### タブ2: 入金履歴
- **CSVアップロードエリア**: ドラッグ&ドロップ or ファイル選択
- **取り込み結果表示**: 自動照合の成功件数・部分一致候補の確認ダイアログ
- **入金記録一覧**: CSVから取り込んだ入金記録のみ表示（照合結果列なし）
  - 入金日、入出金取引番号、振込人名、金額

## 6. CSV自動化について

### 6.1 制約事項
- ゆうちょダイレクトは公開APIを提供していない
- CSVダウンロードはゆうちょダイレクトのWeb画面から手動操作が必要
- **CSVダウンロードの自動化は不可**（ブラウザ自動操作はセキュリティ上推奨できない）

### 6.2 本システムで対応する効率化
- CSVアップロード後の照合処理は完全自動化
- 重複アップロード防止（同一バッチの検出）
- 照合結果のワンクリック確認・手動修正
