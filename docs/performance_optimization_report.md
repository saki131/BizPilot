# パフォーマンス最適化レポート

## 実施した改善

### 1. N+1クエリ問題の解決

**問題点:**
- 納品書一覧取得時、1件の納品書につき明細を個別にクエリ（100件→200クエリ）
- 請求書一覧取得時、1件につき4回以上の追加クエリ（50件→250+クエリ）

**解決策:**
```python
# Before: N+1 problem
delivery_notes = db.query(DeliveryNote).filter(...).all()
# Each note.details access triggers a separate query

# After: Eager loading
delivery_notes = db.query(DeliveryNote)\
    .options(joinedload(DeliveryNote.details))\
    .filter(...).all()
# All data fetched in 1-2 queries
```

**変更ファイル:**
- `backend/routers/delivery_notes.py` - joinedload(DeliveryNote.details)
- `backend/routers/sales_invoices.py` - joinedload multiple relationships
- `backend/routers/contractor_invoices.py` - joinedload all related data

**期待される効果:** 10-50倍の高速化（100ms → 2-10ms）

---

### 2. データベースインデックスの追加

**追加したインデックス:**
```sql
-- delivery_notes
CREATE INDEX ix_delivery_notes_sales_person_id ON delivery_notes(sales_person_id);
CREATE INDEX ix_delivery_notes_tax_rate_id ON delivery_notes(tax_rate_id);
CREATE INDEX ix_delivery_notes_billing_date ON delivery_notes(billing_date);
CREATE INDEX ix_delivery_notes_deleted_flag ON delivery_notes(deleted_flag);

-- delivery_note_details
CREATE INDEX ix_delivery_note_details_delivery_note_id ON delivery_note_details(delivery_note_id);
CREATE INDEX ix_delivery_note_details_product_id ON delivery_note_details(product_id);

-- sales_invoices (同様のパターン)
-- contractor_invoices (同様のパターン)
```

**効果:**
- WHERE句でのフィルタリング高速化（deleted_flag = False）
- JOIN操作の高速化（外部キー検索）
- ORDER BY句の高速化（created_at, billing_date）

**マイグレーションファイル:**
- `backend/alembic/versions/add_foreign_key_indexes.py`

---

## パフォーマンス測定（推定）

| エンドポイント | 改善前 | 改善後 | 改善率 |
|---------------|--------|--------|--------|
| GET /delivery-notes | 300-1000ms | 10-30ms | 10-30x |
| GET /sales-invoices | 500-2000ms | 20-50ms | 15-40x |
| GET /contractor-invoices | 400-1500ms | 15-40ms | 15-35x |

*データ量: 納品書100件、請求書50件を想定*

---

## 追加で検討すべき最適化

### 1. ページネーション実装
```python
@router.get("/")
async def get_delivery_notes(
    skip: int = 0,
    limit: int = 50,  # デフォルト50件まで
    db: Session = Depends(get_db)
):
    return db.query(DeliveryNote)\
        .options(joinedload(DeliveryNote.details))\
        .offset(skip).limit(limit).all()
```

### 2. レスポンスキャッシュ
```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@router.get("/masters/sales-persons")
@cache(expire=300)  # 5分間キャッシュ
async def get_sales_persons(db: Session = Depends(get_db)):
    return db.query(SalesPerson).all()
```

### 3. データベース接続プール最適化
```python
# config.py
SQLALCHEMY_POOL_SIZE = 5
SQLALCHEMY_MAX_OVERFLOW = 10
SQLALCHEMY_POOL_RECYCLE = 3600
```

### 4. 非同期データベースクエリ
- SQLAlchemy async + asyncpg
- 複数のクエリを並列実行可能

### 5. フロントエンドの最適化
- React Query導入でキャッシュとリフェッチ管理
- 仮想スクロール（react-window）で大量データ表示
- データ取得をプリフェッチ

---

## デプロイメモ

1. ✅ コード変更をコミット: `60f3a23`
2. ✅ Dockerfile更新: マイグレーション自動実行 `f771b4a`
3. 🔄 Fly.ioデプロイ中: `flyctl deploy`
4. ⏳ マイグレーション実行: デプロイ時に自動実行される

---

## 今後のモニタリング

### 確認項目:
1. レスポンス時間が短縮されているか（Network tab）
2. データベースクエリ数が削減されているか（SQLAlchemy echo=True）
3. ユーザー体感速度の改善

### ログ確認:
```bash
# Fly.ioログ確認
flyctl logs -a bizpilot-backend

# マイグレーション確認
flyctl ssh console -a bizpilot-backend
alembic current
```

---

## まとめ

**実施した変更:**
- ✅ N+1クエリ問題を解決（joinedload導入）
- ✅ 外部キーとフィルタ列にインデックス追加
- ✅ 自動マイグレーション実行設定

**期待される効果:**
- 納品書・請求書一覧の表示速度が10-30倍高速化
- データベース負荷の大幅削減
- より多くのデータを扱えるスケーラビリティ

**次のステップ:**
- デプロイ完了後にパフォーマンス測定
- 必要に応じてページネーション導入
- キャッシング戦略の検討
