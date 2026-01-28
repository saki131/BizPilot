# デプロイ設計書

## 1. デプロイ概要
システムはVercel、Fly.io、Supabaseの無料枠を使用し、CI/CDパイプラインで自動デプロイします。

## 2. インフラ構成

### フロントエンド (Vercel)
- **プラットフォーム**: Vercel
- **ビルド**: Next.js自動ビルド
- **ドメイン**: vercel.appサブドメイン
- **CDN**: Vercel Edge Network

### バックエンド (Fly.io)
- **プラットフォーム**: Fly.io
- **ランタイム**: Python 3.11 + FastAPI
- **データベース**: Supabase PostgreSQL
- **ストレージ**: Google Drive API

### データベース (Supabase)
- **サービス**: Supabase
- **データベース**: PostgreSQL 15
- **バックアップ**: 自動日次バックアップ
- **レプリケーション**: 自動

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
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_GEMINI_API_KEY=...
```

#### バックエンド (.env)
```
DATABASE_URL=postgresql://...
SECRET_KEY=...
GEMINI_API_KEY=...
GOOGLE_DRIVE_CREDENTIALS=...
JWT_SECRET_KEY=...
```

### 環境別設定
- **開発環境**: ローカル開発
- **ステージング環境**: テスト用デプロイ
- **本番環境**: ユーザー向け

## 5. バックアップ・復元

### データベースバックアップ
- **自動バックアップ**: Supabase自動日次バックアップ
- **手動バックアップ**: pg_dumpコマンド
- **保存期間**: 30日
- **復元テスト**: 月次実施

### ファイルバックアップ
- **Google Drive**: 自動保存
- **ローカルバックアップ**: 重要ファイルの定期バックアップ

## 6. 監視・ログ

### アプリケーション監視
- **Vercel Analytics**: パフォーマンス監視
- **Fly.io Metrics**: サーバー監視
- **Supabase Dashboard**: データベース監視

### ログ管理
- **アプリケーションログ**: 構造化ログ出力
- **エラーログ**: Sentryまたは類似サービス
- **アクセスログ**: 各プラットフォームのログ

## 7. スケーリング

### 無料枠制限
- **Vercel**: 100GB/月、1000関数実行/月
- **Fly.io**: 3GB RAM、160GB/月転送
- **Supabase**: 500MBデータベース、50MBファイルストレージ

### スケーリング戦略
- **垂直スケーリング**: メモリ/CPU増加
- **水平スケーリング**: 複数インスタンス
- **キャッシュ**: Redis導入（将来）

## 8. ロールバック

### デプロイロールバック
- **Vercel**: 自動ロールバック機能
- **Fly.io**: 以前のリリースへのロールバック
- **データベース**: ポイントインタイムリカバリ

### 手順
1. 問題検知
2. ロールバック実行
3. 影響調査
4. 修正・再デプロイ