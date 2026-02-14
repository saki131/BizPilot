# ステージング環境セットアップガイド

## 概要

BizPilot のステージング環境は完全無料枠で構築されており、`backlog` ブランチへの push で自動デプロイされます。

## 環境構成

| 環境 | ブランチ | フロントエンド | バックエンド | データベース |
|------|---------|--------------|------------|------------|
| **ローカル** | - | localhost:3000 | localhost:8000 | Docker PostgreSQL |
| **ステージング** | backlog | Vercel (backlog) | Fly.io staging | Supabase staging |
| **本番** | master | Vercel (master) | Fly.io | Supabase |

## セットアップ手順

### 1. Supabase ステージング DB 作成

1. [Supabase Dashboard](https://app.supabase.com/) にアクセス
2. 「New Project」をクリック
3. プロジェクト設定：
   - **Name**: `bizpilot-staging`
   - **Database Password**: 強力なパスワード（保存しておく）
   - **Region**: `Tokyo (ap-northeast-1)` または `Oregon (us-west-1)`
   - **Pricing Plan**: `Free` を選択
4. プロジェクト作成完了を待つ（約2分）
5. 接続情報を取得：
   - Settings → Database → Connection string
   - URI 形式をコピー（例: `postgresql://postgres.xxx:[YOUR-PASSWORD]@xxx.supabase.co:5432/postgres`）

### 2. Fly.io ステージングアプリ作成

```powershell
cd C:\Users\Owner\workspace\BizPilot\backend

# ステージングアプリ作成
flyctl apps create bizpilot-backend-staging --org personal

# 環境変数設定
flyctl secrets set -a bizpilot-backend-staging `
  DATABASE_URL="postgresql://postgres.xxx:[YOUR-PASSWORD]@xxx.supabase.co:5432/postgres" `
  SECRET_KEY="staging-secret-key-change-this-to-random-string" `
  GEMINI_KEY="your-gemini-api-key" `
  GEMINI_KEY_1="key1-if-multiple" `
  GEMINI_KEY_2="key2-if-multiple"

# 初回デプロイ
flyctl deploy -a bizpilot-backend-staging -c fly.staging.toml
```

### 3. データベース初期化

```powershell
# Fly.io コンソールに接続
flyctl ssh console -a bizpilot-backend-staging

# マイグレーション実行
cd /app
alembic upgrade head

# マスタデータ投入
python seed_master_data.py

# 終了
exit
```

### 4. Vercel 環境変数設定

Vercel Dashboard または CLI で設定：

```powershell
cd C:\Users\Owner\workspace\BizPilot\frontend

# backlog ブランチ用の環境変数を設定
vercel env add NEXT_PUBLIC_API_URL
# Environment を選択: Preview
# Branch を選択: backlog
# 値を入力: https://bizpilot-backend-staging.fly.dev/api
```

または Vercel Dashboard で：
1. プロジェクト設定 → Environment Variables
2. 追加：
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://bizpilot-backend-staging.fly.dev/api`
   - **Environment**: `Preview`
   - **Git Branch**: `backlog`

### 5. Git ブランチ戦略

```powershell
# backlog/master ブランチを作成（初回のみ）
git checkout -b backlog/master

# 開発が完了したら backlog/master にマージ
git checkout backlog/master
git merge develop  # または feature ブランチ

# backlog/master に push すると自動的にステージング環境にデプロイされる
git push origin backlog/master

# ステージング環境で問題なければ master にマージして本番デプロイ
git checkout master
git merge backlog/master
git push origin master
```

## デプロイフロー

```
開発ブランチ → backlog/master ブランチ → master ブランチ
    ↓              ↓                      ↓
  ローカル      ステージング            本番環境
```

## 自動デプロイの確認

### フロントエンド（Vercel）
- `backlog/master` ブランチへの push で自動デプロイ
- デプロイ URL: Vercel Dashboard の Deployments タブで確認
- 通常 `https://bizpilot-{random}.vercel.app` の形式

### バックエンド（Fly.io）
- 手動デプロイが必要（無料枠の制約）
- デプロイコマンド：
  ```powershell
  cd backend
  flyctl deploy -a bizpilot-backend-staging -c fly.staging.toml
  ```

## 環境のリセット

### データベースのリセット
```powershell
flyctl ssh console -a bizpilot-backend-staging
cd /app
alembic downgrade base
alembic upgrade head
python seed_master_data.py
exit
```

### アプリの再起動
```powershell
flyctl apps restart bizpilot-backend-staging
```

## トラブルシューティング

### ログの確認
```powershell
# バックエンドログ
flyctl logs -a bizpilot-backend-staging

# フロントエンドログ
# Vercel Dashboard → Deployments → 該当デプロイ → Logs
```

### データベース接続確認
```powershell
flyctl ssh console -a bizpilot-backend-staging
python -c "from database import SessionLocal; db = SessionLocal(); print('DB Connected!'); db.close()"
```

### 環境変数確認
```powershell
flyctl secrets list -a bizpilot-backend-staging
```

## コスト管理

### 無料枠の制約
- **Supabase**: 500MB データベース、2プロジェクトまで
- **Fly.io**: 3台の shared-cpu-1x VM（月160時間）、256MB RAM
- **Vercel**: プレビューデプロイは無制限（無料）

### 無料枠を超えないために
1. ステージング DB は定期的にクリーンアップ
2. 画像ファイルは最小限に
3. 不要なデプロイは削除

## セキュリティ

### 秘密情報の管理
- `.env` ファイルは Git にコミットしない
- Fly.io Secrets で環境変数を管理
- Vercel の Environment Variables で管理

### アクセス制限
- ステージング環境も本番同様に JWT 認証を使用
- API キーは本番と別のものを使用推奨
