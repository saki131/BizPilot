# デプロイ設計書

## 1. デプロイ概要
システムはVercel、Fly.io、Neon PostgreSQLを使用し、ブランチ戦略に基づいて本番/ステージングへデプロイします。

## 2. インフラ構成

### フロントエンド (Vercel)
- **プラットフォーム**: Vercel
- **ビルド**: Next.js自動ビルド
- **ドメイン**: vercel.appサブドメイン
- **CDN**: Vercel Edge Network

### バックエンド (Fly.io)
- **プラットフォーム**: Fly.io
- **ランタイム**: Python 3.11 + FastAPI
- **本番アプリ**: `bizpilot-backend`
- **ステージングアプリ**: `bizpilot-backend-staging`
- **コンテナ**: Docker (Dockerfile in `backend/`)

### データベース (Neon PostgreSQL)
- **サービス**: Neon PostgreSQL
- **リージョン**: ap-southeast-1 (シンガポール)
- **接続**: Pooler接続 (`-pooler.ap-southeast-1.aws.neon.tech`)
- **SSL**: `sslmode=require` 必須
- **バックアップ**: Neon 自動バックアップ

## 3. CI/CDパイプライン

### GitHub Actionsワークフロー
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    - name: Install dependencies
      run: npm ci
    - name: Run tests
      run: npm test
    - name: Build
      run: npm run build

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to Vercel
      run: vercel --prod

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to Fly.io
      run: fly deploy
```

## 4. 環境管理

### 環境変数
#### フロントエンド (.env.local)
```
NEXT_PUBLIC_API_URL=https://bizpilot-backend.fly.dev
```

#### バックエンド (.env)
```
DATABASE_URL=postgresql://neondb_owner:...@ep-xxx-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
SECRET_KEY=<ランダムな長文字列>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
GEMINI_KEY=<APIキー>              # 単体キー（後方互換）
GEMINI_KEY_1=<APIキー1>          # 複数キーローテーション用
GEMINI_KEY_2=<APIキー2>
# 会社情報
COMPANY_NAME=
COMPANY_REPRESENTATIVE=
COMPANY_POSTAL_CODE=
COMPANY_ADDRESS1=
COMPANY_ADDRESS2=
COMPANY_BRANCH_NAME=
COMPANY_REGISTRATION_NUMBER=
# 振込先情報
BANK_NAME=
BANK_BRANCH_NAME=
BANK_ACCOUNT_TYPE=普通
BANK_ACCOUNT_NUMBER=
BANK_ACCOUNT_HOLDER=
BANK_YUCHO_SYMBOL=
BANK_YUCHO_NUMBER=
```

> **重要**: `.env` は Git 管理外 (`.gitignore` 追加済み)。テンプレートは `.env.example` を参照。  
> 本番・ステージング環境の秘密情報は `flyctl secrets set` で管理します。

```bash
# Fly.io Secrets 設定例（本番）
flyctl secrets set COMPANY_NAME="..." BANK_NAME="..." -a bizpilot-backend
# ステージング
flyctl secrets set COMPANY_NAME="..." BANK_NAME="..." -a bizpilot-backend-staging
```

### 環境別設定
- **開発環境**: ローカル開発 (`.env` ファイル使用)
- **ステージング環境**: Fly.io Secrets + Vercel 環境変数
- **本番環境**: Fly.io Secrets + Vercel 環境変数

## 5. バックアップ・復元

### データベースバックアップ
- **自動バックアップ**: Neon 自動バックアップ
- **手動バックアップ**: pg_dumpコマンド
- **保存期間**: Neon プランに依存
- **復元テスト**: 月次実施

### ファイルバックアップ
- **Google Drive**: 自動保存
- **ローカルバックアップ**: 重要ファイルの定期バックアップ

## 6. 監視・ログ

### アプリケーション監視
- **Vercel Analytics**: パフォーマンス監視
- **Fly.io Metrics**: サーバー監視
- **Neon Dashboard**: データベース監視

### ログ管理
- **アプリケーションログ**: 構造化ログ出力
- **エラーログ**: Sentryまたは類似サービス
- **アクセスログ**: 各プラットフォームのログ

## 7. スケーリング

### 無料枠制限
- **Vercel**: 100GB/月、1000関数実行/月
- **Fly.io**: 3GB RAM、160GB/月転送
- **Neon**: 0.5 GiB ストレージ (Free プラン)、10 GiB 転送

### スケーリング戦略
- **垂直スケーリング**: メモリ/CPU増加
- **水平スケーリング**: 複数インスタンス
- **キャッシュ**: Redis導入（将来）

## 8. ロールバック

### デプロイロールバック
- **Vercel**: 自動ロールバック機能
- **Fly.io**: 以前のリリースへのロールバック
- **データベース**: Neon ポイントインタイムリカバリ

### 手順
1. 問題検知
2. ロールバック実行
3. 影響調査
4. 修正・再デプロイ