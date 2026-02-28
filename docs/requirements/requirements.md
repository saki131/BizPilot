# 請求書出力アプリ要件定義書（Next.js + FastAPI版）

## 1. システム概要
販売員の納品書を管理し、月次で請求書を自動生成する業務システム。委託先の請求書も独立して管理する。手書き納品書の画像から自動的にデータを抽出する最先端のAI機能を搭載。

## 2. 技術要件

### 2.1 技術スタック

#### フロントエンド
- **フレームワーク**: Next.js 14 (App Router)
- **言語**: TypeScript 5.x
- **スタイリング**: Tailwind CSS 3.x
- **UIコンポーネント**: shadcn/ui
- **状態管理**: TanStack Query (React Query) v5
- **フォーム管理**: React Hook Form + Zod
- **日付処理**: date-fns
- **アイコン**: Lucide React
- **画像処理**: react-dropzone, react-image-crop

#### バックエンド
- **フレームワーク**: FastAPI 0.104+
- **言語**: Python 3.11+
- **ORM**: SQLAlchemy 2.0
- **マイグレーション**: Alembic
- **バリデーション**: Pydantic v2
- **認証**: JWT (python-jose)
- **非同期処理**: asyncio, httpx

#### データベース
- **RDBMS**: PostgreSQL 15

#### 外部API・サービス
- **AI/OCR**: Google Gemini API (gemini-1.5-flash)
- **PDF生成**: ReportLab (Python)

#### デプロイ・インフラ
- **フロントエンド**: Vercel (無料枠)
  - 本番: master ブランチ
  - ステージング: backlog/master ブランチ（自動デプロイ）
- **バックエンド**: Fly.io (無料枠)
  - 本番: bizpilot-backend
  - ステージング: bizpilot-backend-staging
- **データベース**: Neon PostgreSQL
  - 本番・ステージング共用: ap-southeast-1 リージョン

#### 開発ツール
- **IDE**: Visual Studio Code
- **パッケージ管理**: npm / pnpm (Frontend), Poetry (Backend)
- **コード品質**: ESLint, Prettier, Black, Ruff
- **型チェック**: TypeScript, mypy

### 2.2 アーキテクチャ
```
┌─────────────────────────────────────┐
│         Next.js Frontend            │
│  (Vercel - SSR/CSR Hybrid)         │
│  - モバイルファーストUI             │
│  - リアルタイム更新                 │
│  - 画像プレビュー・編集             │
└──────────────┬──────────────────────┘
               │ REST API
               │ (JSON)
┌──────────────▼──────────────────────┐
│         FastAPI Backend             │
│  (Fly.io - 非同期処理)             │
│  - ビジネスロジック                 │
│  - Gemini API連携                   │
│  - Google Drive連携                 │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼──────┐      ┌──────▼─────────┐
│PostgreSQL│      │ External APIs  │
│(Supabase)│      │ - Gemini API   │
│          │      │ - Drive API    │
└──────────┘      └────────────────┘
```

## 3. 機能要件

### 3.1 認証機能
- **JWT認証**: アクセストークン + リフレッシュトークン
- 管理者のみがシステムを利用
- セッション有効期限: 1時間（自動延長あり）
- セキュアなパスワードハッシュ化（bcrypt）

### 3.2 マスタ管理機能

#### 3.2.1 販売員管理
- 販売員情報のCRUD（最大50名想定）
- 削除フラグによる論理削除
- 一覧表示（ページネーション、検索、ソート）

#### 3.2.2 委託先管理
- 委託先情報のCRUD（10社程度想定）
- 削除フラグによる論理削除

#### 3.2.3 商品管理
- 商品情報のCRUD（39品目）
- 各種フラグ管理（割引対象外、ノルマ対象等）
- 表示順の並べ替え（ドラッグ&ドロップ）

#### 3.2.4 税率管理
- 税率設定（デフォルト10%）
- 将来的な税率変更に対応

#### 3.2.5 割引率管理
- 割引率マスタ管理（0%〜40%）

### 3.3 納品書管理機能

#### 3.3.1 納品書画像認識機能（コア機能）

**処理フロー:**
1. **画像アップロード**
   - ドラッグ&ドロップ
   - ファイル選択
   - モバイルカメラ直接撮影
   - 複数画像の一括アップロード対応

2. **AI解析（Gemini API）**
   - 画像をBase64エンコードして送信
   - 手書き文字を認識
   - マスタデータと照合
   - JSON形式でデータ抽出

3. **リアルタイム進捗表示**
   - アップロード進捗
   - AI解析進捗
   - データ検証進捗

4. **認識結果確認画面**
   - 左側: 元画像（ズーム・パン可能）
   - 右側: 抽出データ編集フォーム
   - リアルタイムバリデーション
   - 商品明細の追加・削除・編集

5. **データ保存**
   - PostgreSQLにデータ保存
   - 元画像をGoogle Driveに自動アップロード
   - ファイルパスをDBに保存

**Gemini API プロンプト仕様:**
```
納品書の画像を解析して、以下のJSON形式で情報を抽出してください。

マスタデータ:
販売員: [販売員一覧]
税率: [税率一覧]
商品: [商品一覧]

【商品名の読み取りルール】
- 「"」や省略記号は直前の商品名を継承
- 「シャンプー」→「ハイシャンプー」
- 「リンス」→「リンス＆ヘアパック」

【数値の読み取りルール】
- 数量: 整数
- 単価: 円単位
- 税抜合計金額の整合性チェック必須

【成功条件】
全項目が特定でき、金額が一致する場合のみsuccess: true

出力JSON形式:
成功時: { "success": true, "salesPersonId": "1", ... }
失敗時: { "success": false, "failureReason": "..." }
```

**認識精度向上策:**
- プロンプトエンジニアリング
- 商品マスタとの曖昧マッチング（Levenshtein距離）
- 和暦→西暦自動変換
- 金額計算の自動検証

#### 3.3.2 納品書CRUD機能
- 新規登録（手動入力 or 画像認識）
- 編集・削除
- 一覧表示（フィルタ、検索、ソート）
- 詳細表示
- PDF生成・ダウンロード

#### 3.3.3 納品書明細管理
- 商品選択（オートコンプリート）
- 数量・単価入力
- 金額自動計算
- ノルマ対象/対象外の自動判定

### 3.4 請求書生成機能

#### 3.4.1 販売員請求書
**集計期間**: 毎月21日〜翌月20日

**割引率適用ルール（自動適用）:**
| 割引率 | 下限額 | 備考 |
|--------|--------|------|
| 40% | 400,000円以上 | 自動適用 |
| 30% | 200,000円以上 | 自動適用 |
| 20% | 42,000円以上 | 自動適用 |
| 0% | 42,000円未満 | 自動適用、後で10%に変更可能 |

**自動計算項目:**
- ノルマ対象金額・割引額・割引後金額
- ノルマ対象外金額・割引額・割引後金額
- 合計金額（税抜・税込）
- 消費税額

**一括作成機能:**
- 販売員選択: 全体 or 個別選択
- 締め日指定: 必須（例: 2025-12-20）
- 期間は自動計算（前月21日〜締め日）
- 複数の請求書を一括生成
- 割引率20%未満の場合は0%で生成し、後で10%に変更可能

#### 3.4.2 委託先請求書
**割引率適用ルール:**
| 割引率 | 下限額 |
|--------|--------|
| 20% | 0円 |
| 30% | 200,000円 |
| 40% | 400,000円 |

### 3.5 PDF出力機能
- ReportLabでサーバー側生成
- 提供テンプレート完全準拠
- ユニバーサルデザイン対応（大きな文字、高コントラスト）
- Google Driveに自動保存

### 3.6 領収管理機能
- 領収日の入力・更新
- 未収金一覧表示
- 支払い状況フィルタ

### 3.7 ダッシュボード
- 当月の納品書件数
- 未請求金額
- 未収金額
- 最近の活動
- グラフによる可視化（Chart.js / Recharts）

## 4. 非機能要件

### 4.1 性能要件
- **ページ読み込み**: 2秒以内（First Contentful Paint）
- **API応答時間**: 500ms以内（通常操作）
- **一覧取得API**: 100ms以内（N+1クエリ防止のため eager loading 実装）
- **画像認識処理**: 5-10秒以内
- **同時接続**: 10ユーザー対応

### 4.2 環境構成

#### 環境一覧
| 環境 | 用途 | URL/接続先 | データベース |
|------|------|-----------|-------------|
| Local | ローカル開発 | localhost:3000 / localhost:8000 | Neon PostgreSQL (`.env` で接続) |
| Staging | テスト環境 | staging.bizpilot.vercel.app / bizpilot-backend-staging.fly.dev | Neon PostgreSQL |
| Production | 本番環境 | bizpilot.vercel.app / bizpilot-backend.fly.dev | Neon PostgreSQL |

#### ブランチ戦略
```
develop (開発ブランチ)
  ↓
backlog/master (ステージング用ブランチ)
  ↓ 自動デプロイ → Staging環境
  ↓ レビュー・検証
master (本番ブランチ)
  ↓ 自動デプロイ → Production環境
```

#### デプロイフロー
1. **開発**: `develop` ブランチで機能開発
2. **ステージング**: `backlog/master` ブランチへマージ → Vercel & Fly.io 自動デプロイ
3. **検証**: ステージング環境でテスト実施
4. **本番リリース**: `master` ブランチへマージ → 本番環境へ自動デプロイ

#### 環境変数管理
- `.env` ファイルは Git 管理外（`.gitignore` に追加済み）
- `.env.example` をテンプレートとして利用
- 環境ごとに異なる設定:
  - `DATABASE_URL`: Neon PostgreSQL 接続文字列
  - `SECRET_KEY`: JWT署名キー
  - `ALGORITHM`: JWTアルゴリズム（デフォルト: HS256）
  - `ACCESS_TOKEN_EXPIRE_MINUTES`: アクセストークン有効期限（デフォルト: 60分）
  - `REFRESH_TOKEN_EXPIRE_DAYS`: リフレッシュトークン有効期限（デフォルト: 7日）
  - `GEMINI_KEY`: Gemini API認証キー（単体）
  - `GEMINI_KEY_1`, `GEMINI_KEY_2`, ...: 複数Gemini APIキー（ローテーション対応）
  - `GEMINI_KEYS`: カンマ区切りの複数APIキー（代替形式）
  - `NEXT_PUBLIC_API_URL`: バックエンドAPIエンドポイント
  - `COMPANY_NAME`, `COMPANY_REPRESENTATIVE`, `COMPANY_POSTAL_CODE`: 会社情報
  - `COMPANY_ADDRESS1`, `COMPANY_ADDRESS2`, `COMPANY_BRANCH_NAME`: 会社住所・拠点名
  - `COMPANY_REGISTRATION_NUMBER`: インボイス登録番号
  - `BANK_NAME`, `BANK_BRANCH_NAME`, `BANK_ACCOUNT_TYPE`: 振込先銀行情報
  - `BANK_ACCOUNT_NUMBER`, `BANK_ACCOUNT_HOLDER`: 口座番号・名義
  - `BANK_YUCHO_SYMBOL`, `BANK_YUCHO_NUMBER`: ゆうちょ記号・番号
- 本番・ステージング環境の秘密情報は Fly.io Secrets で管理（`flyctl secrets set`）

詳細なセットアップ手順は [STAGING_SETUP.md](../STAGING_SETUP.md) を参照。

### 4.3 セキュリティ要件
- HTTPS通信必須
- JWT認証
- CORS設定
- XSS/CSRF対策
- SQLインジェクション対策（ORM使用）
- 機密情報の環境変数管理

### 4.3 可用性要件
- 稼働率: 99%以上（月間ダウンタイム7時間以内）
- 自動バックアップ: 毎日1回
- バックアップ保存期間: 30日
- 週次フルバックアップ: 12ヶ月保存

### 4.4 ユーザビリティ要件
- **モバイルファースト設計**
- **レスポンシブ対応**: スマートフォン、タブレット、PC
- **ユニバーサルデザイン**:
  - 最小文字サイズ: 16px
  - 行間: 1.6倍
  - コントラスト比: WCAG AA準拠
  - タップ領域: 最小44×44px
- **高齢者対応**:
  - 大きなボタン
  - わかりやすいラベル
  - エラーメッセージは平易な日本語

## 5. データベース設計

### 5.1 主要テーブル

#### users（管理者）
```sql
- user_id: INTEGER PRIMARY KEY (SERIAL)
- username: VARCHAR(100) UNIQUE NOT NULL
- hashed_password: VARCHAR(255) NOT NULL
- deleted_flag: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### sales_persons（販売員）
```sql
- sales_person_id: INTEGER PRIMARY KEY (SERIAL)
- name: VARCHAR(100) NOT NULL
- deleted_flag: BOOLEAN DEFAULT FALSE
- display_order: INTEGER DEFAULT 0
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### products（商品）
```sql
- product_id: INTEGER PRIMARY KEY (SERIAL)
- name: VARCHAR(200) NOT NULL
- price: INTEGER NOT NULL
- discount_exclusion_flag: BOOLEAN DEFAULT FALSE
- quota_exclusion_flag: BOOLEAN DEFAULT FALSE
- quota_target_flag: BOOLEAN DEFAULT FALSE
- deleted_flag: BOOLEAN DEFAULT FALSE
- display_order: INTEGER DEFAULT 0
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### contractors（委託先）
```sql
- contractor_id: INTEGER PRIMARY KEY (SERIAL)
- name: VARCHAR(100) NOT NULL
- deleted_flag: BOOLEAN DEFAULT FALSE
- display_order: INTEGER DEFAULT 0
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### tax_rates（税率）
```sql
- tax_rate_id: INTEGER PRIMARY KEY (SERIAL)
- rate: DECIMAL(4,2) NOT NULL
- display_name: VARCHAR(20) NOT NULL
- deleted_flag: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### discount_rates（割引率）
```sql
- discount_rate_id: INTEGER PRIMARY KEY (SERIAL)
- rate: DECIMAL(4,2) NOT NULL        -- 保存形式: 小数(0.20) or 整数(20) が混在する可能性あり
- threshold_amount: INTEGER DEFAULT 0 -- 割引適用下限金額
- sales_person_flag: BOOLEAN DEFAULT TRUE  -- True=販売員向け, False=委託先向け
- deleted_flag: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### delivery_notes（納品書）
```sql
- delivery_note_id: UUID PRIMARY KEY
- sales_person_id: INTEGER REFERENCES sales_persons(sales_person_id)
- tax_rate_id: INTEGER REFERENCES tax_rates(tax_rate_id)
- quota_amount: INTEGER DEFAULT 0
- non_quota_amount: INTEGER DEFAULT 0
- tax_amount: INTEGER DEFAULT 0
- total_amount_ex_tax: INTEGER DEFAULT 0
- total_amount_inc_tax: INTEGER DEFAULT 0
- remarks: TEXT
- file_path: VARCHAR(500)
- image_filename: VARCHAR(500)  -- アップロード画像ファイル名
- delivery_date: TIMESTAMP NOT NULL
- billing_date: TIMESTAMP NOT NULL
- image_recognition_data: JSON  -- Gemini APIレスポンス保存用
- deleted_flag: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### delivery_note_details（納品書明細）
```sql
- delivery_note_detail_id: UUID PRIMARY KEY
- delivery_note_id: UUID REFERENCES delivery_notes(delivery_note_id) ON DELETE CASCADE
- product_id: INTEGER REFERENCES products(product_id)
- quantity: INTEGER NOT NULL
- unit_price: INTEGER NOT NULL
- amount: INTEGER NOT NULL
- remarks: VARCHAR(200)
- deleted_flag: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### sales_invoices（販売員請求書）
```sql
- sales_invoice_id: UUID PRIMARY KEY
- sales_person_id: INTEGER REFERENCES sales_persons(sales_person_id) NOT NULL
- tax_rate_id: INTEGER REFERENCES tax_rates(tax_rate_id) NOT NULL
- discount_rate_id: INTEGER REFERENCES discount_rates(discount_rate_id) NOT NULL
- invoice_date: DATE
- receipt_date: DATE
- note: VARCHAR(500)                  -- 但し書き
- non_discountable_amount: INTEGER DEFAULT 0
- quota_subtotal: INTEGER DEFAULT 0   -- ノルマ対象小計
- quota_discount_amount: INTEGER DEFAULT 0
- quota_total: INTEGER DEFAULT 0
- non_quota_subtotal: INTEGER DEFAULT 0
- non_quota_discount_amount: INTEGER DEFAULT 0
- non_quota_total: INTEGER DEFAULT 0
- total_amount_ex_tax: INTEGER DEFAULT 0
- tax_amount: INTEGER DEFAULT 0
- total_amount_inc_tax: INTEGER DEFAULT 0
- deleted_flag: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### sales_invoice_details（販売員請求書明細）
```sql
- sales_invoice_detail_id: UUID PRIMARY KEY
- sales_invoice_id: UUID REFERENCES sales_invoices(sales_invoice_id) ON DELETE CASCADE
- product_id: INTEGER REFERENCES products(product_id)
- total_quantity: INTEGER DEFAULT 0
- unit_price: INTEGER NOT NULL
- amount: INTEGER NOT NULL
- deleted_flag: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### contractor_invoices（委託先請求書）
```sql
- contractor_invoice_id: UUID PRIMARY KEY
- contractor_id: INTEGER REFERENCES contractors(contractor_id) NOT NULL
- discount_rate_id: INTEGER REFERENCES discount_rates(discount_rate_id) NOT NULL
- tax_rate_id: INTEGER REFERENCES tax_rates(tax_rate_id) NOT NULL
- invoice_date: DATE NOT NULL
- receipt_date: DATE
- payment_due_date: DATE
- note: VARCHAR(500)
- non_discountable_amount: INTEGER DEFAULT 0
- quota_subtotal: INTEGER DEFAULT 0
- quota_discount_amount: INTEGER DEFAULT 0
- quota_total: INTEGER DEFAULT 0
- non_quota_subtotal: INTEGER DEFAULT 0
- non_quota_discount_amount: INTEGER DEFAULT 0
- non_quota_total: INTEGER DEFAULT 0
- total_amount_ex_tax: INTEGER DEFAULT 0
- total_discount_amount: INTEGER DEFAULT 0
- total_after_discount: INTEGER DEFAULT 0
- tax_amount: INTEGER DEFAULT 0
- total_amount_inc_tax: INTEGER DEFAULT 0
- deleted_flag: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

#### contractor_invoice_details（委託先請求書明細）
```sql
- contractor_invoice_detail_id: UUID PRIMARY KEY
- contractor_invoice_id: UUID REFERENCES contractor_invoices(contractor_invoice_id) ON DELETE CASCADE
- product_id: INTEGER REFERENCES products(product_id)
- total_quantity: INTEGER DEFAULT 0
- unit_price: INTEGER NOT NULL
- amount: INTEGER NOT NULL
- deleted_flag: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()
```

### 5.2 インデックス設計
```sql
CREATE INDEX idx_delivery_notes_sales_person ON delivery_notes(sales_person_id);
CREATE INDEX idx_delivery_notes_date ON delivery_notes(delivery_date);
CREATE INDEX idx_delivery_note_details_delivery_note ON delivery_note_details(delivery_note_id);
```

## 6. API設計

### 6.1 認証API
```
POST   /api/auth/login          ログイン
POST   /api/auth/refresh        トークン更新
POST   /api/auth/logout         ログアウト
```

### 6.2 マスタAPI
```
GET    /api/sales-persons       販売員一覧
POST   /api/sales-persons       販売員作成
GET    /api/sales-persons/{id}  販売員詳細
PUT    /api/sales-persons/{id}  販売員更新
DELETE /api/sales-persons/{id}  販売員削除

（商品、委託先、税率、割引率も同様）
```

### 6.3 納品書API
```
POST   /api/delivery-notes/recognize-image    画像認識
GET    /api/delivery-notes                    一覧取得
POST   /api/delivery-notes                    作成
GET    /api/delivery-notes/{id}               詳細取得
PUT    /api/delivery-notes/{id}               更新
DELETE /api/delivery-notes/{id}               削除
GET    /api/delivery-notes/{id}/pdf           PDF生成
```

### 6.4 請求書API
```
POST   /api/sales-invoices/bulk-generate      一括生成（販売員選択+締め日）
PATCH  /api/sales-invoices/{id}/discount-rate 割引率変更（0%→10%）
GET    /api/sales-invoices                    一覧取得
GET    /api/sales-invoices/{id}               詳細取得
GET    /api/sales-invoices/{id}/pdf           PDF取得

（委託先請求書も同様）
```

## 7. 画面設計

### 7.1 画面一覧
1. ログイン画面
2. ダッシュボード
3. 納品書管理
   - 一覧画面
   - **画像アップロード画面**
   - **認識結果確認画面**
   - 詳細画面
   - 編集画面
4. 請求書管理
   - 販売員請求書一覧
   - 委託先請求書一覧
   - 詳細画面
5. マスタ管理
   - 販売員一覧
   - 商品一覧
   - 委託先一覧
6. 領収管理画面
7. 設定画面

### 7.2 主要画面のUI/UX

#### 納品書画像アップロード画面
```tsx
- 大きなドロップゾーン（画面中央）
- カメラアイコンとファイルアイコン
- 「タップして撮影」「ファイルを選択」
- アップロード済み画像のサムネイル一覧
- 一括アップロードプログレスバー
```

#### 認識結果確認画面（2カラムレイアウト）
```tsx
左側:
  - 元画像表示（拡大・縮小・パン）
  - 画像回転機能
  
右側:
  - 販売員選択（オートコンプリート）
  - 納品日（カレンダーピッカー）
  - 商品明細テーブル
    - 商品名（オートコンプリート）
    - 数量（数値入力）
    - 単価（自動入力）
    - 金額（自動計算）
    - 削除ボタン
  - 商品追加ボタン
  - 合計金額表示（リアルタイム更新）
  - 保存ボタン / キャンセルボタン
```

## 8. 開発スケジュール

### Phase 1: 環境構築・基盤（2週間）
- **Week 1**: 
  - プロジェクトセットアップ
  - Next.js + FastAPI初期設定
  - データベース設計・構築
  - 初期マスタデータ投入
- **Week 2**:
  - 認証機能実装
  - 基本レイアウト作成
  - 共通コンポーネント作成

### Phase 2: マスタ管理・基本CRUD（2週間）
- **Week 3**:
  - 販売員・商品・委託先CRUD
  - 一覧画面（ページネーション、検索、ソート）
- **Week 4**:
  - マスタ管理画面完成
  - バリデーション実装

### Phase 3: 納品書機能（3週間）
- **Week 5**:
  - 納品書CRUD（手動入力）
  - 商品明細の動的追加
- **Week 6**:
  - Gemini API統合
  - 画像アップロード機能
  - 画像認識ロジック実装
- **Week 7**:
  - 認識結果確認画面
  - データ検証・補正ロジック
  - エラーハンドリング

### Phase 4: 請求書機能（2週間）
- **Week 8**:
  - 請求書生成ロジック
  - 割引計算実装
- **Week 9**:
  - PDF生成機能
  - Google Drive連携
過去に認識した画像ですが登録しますか？
### Phase 5: UI/UX改善・最適化（2週間）
- **Week 10**:
  - モバイル最適化
  - ユニバーサルデザイン適用
  - アニメーション・トランジション
- **Week 11**:
  - パフォーマンス最適化
  - アクセシビリティ対応

### Phase 6: テスト・デプロイ（1週間）
- **Week 12**:
  - 統合テスト
  - 本番デプロイ
  - 運用ドキュメント作成

**合計開発期間: 12週間（約3ヶ月）**

## 9. リスク管理

### 9.1 技術リスク
- Gemini API無料枠制限（1500リクエスト/日）
- 手書き文字認識精度
- Vercel/Fly.io無料枠の制約

### 9.2 対応策
- API使用量監視ダッシュボード
- プロンプト最適化による精度向上
- 不鮮明画像の再撮影促進UI
- 無料枠超過時のアラート

## 10. 提供データ

### 初期マスタデータ
✅ 販売員32名
✅ 商品39品目
✅ 委託先5社
✅ 税率1件（10%）
✅ 割引率5段階

### テンプレート
✅ 納品書テンプレート
✅ 販売員請求書テンプレート
✅ 委託先請求書テンプレート

## 11. 成功指標（KPI）

- 画像認識成功率: 90%以上
- 認識処理時間: 10秒以内
- ページ読み込み: 2秒以内
- モバイルユーザビリティスコア: 90点以上
- エラー発生率: 1%未満