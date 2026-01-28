# 請求書管理システム 起動ガイド

## 概要
このシステムは、FastAPI（バックエンド）とNext.js（フロントエンド）で構成された請求書管理システムです。

## 前提条件
- Python 3.11+
- Node.js 18+
- PostgreSQL（Supabase）

## バックエンド起動方法

### 1. 仮想環境のアクティブ化
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windowsの場合
```

### 2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 3. データベースマイグレーション
```bash
alembic upgrade head
```

### 4. サーバー起動

**オプション1: backendディレクトリから起動（推奨）**
```bash
# backendディレクトリにいる状態で
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

**オプション2: workspaceディレクトリから起動**
```bash
cd backend; python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

**注意**: オプション2の場合、Pythonパスが正しく設定されている必要があります。

### アクセス先
- API: http://localhost:8002
- Swagger UI: http://localhost:8002/docs

## フロントエンド起動方法

### 1. ディレクトリ移動
```bash
cd frontend
```

### 2. 依存関係のインストール
```bash
npm install
```

### 3. 開発サーバー起動

#### 開発モード（推奨）
```bash
npm run dev -- -H 0.0.0.0 -p 3000
```

#### 本番モード
```bash
# ビルド
npm run build

# 起動
npm run start -- -H 0.0.0.0 -p 3000
```

### アクセス先
- ローカル: http://localhost:3000
- ネットワーク: http://172.16.0.71:3000（モバイルからもアクセス可能）
- ログイン画面: http://localhost:3000/login

## システムテスト

### 1. ログイン
- URL: http://localhost:3000/login
- テストユーザー: admin / password123

### 2. 機能テスト
- ダッシュボード: http://localhost:3000/dashboard
- マスタ管理: http://localhost:3000/masters
- 納品書管理: http://localhost:3000/delivery-notes
- 請求書管理: http://localhost:3000/invoices

### 3. 新機能テスト（請求書一括生成）
- 請求書画面で「一括請求書生成」ボタンをクリック
- 締め日を入力（例: 2026-01-20）
- 販売員を選択（全体 or 個別）
- 割引率は金額に応じて自動適用（0%, 20%, 30%, 40%）
- 0%請求書は「10%に変更」ボタンで変更可能

## トラブルシューティング

### ポート競合
- バックエンド: ポート8002が使用中の場合、別のポートを指定
- フロントエンド: ポート3000が使用中の場合、自動で3001などに変更

### プロセス終了
```bash
# Node.jsプロセス終了
taskkill /f /im node.exe

# Pythonプロセス終了
taskkill /f /im python.exe
```

### 依存関係エラー
- バックエンド: `pip install -r requirements.txt` を再実行
- フロントエンド: `npm install` を再実行

## 環境変数
必要に応じて以下の環境変数を設定してください：
- `DATABASE_URL`: PostgreSQL接続文字列
- `SECRET_KEY`: JWTシークレットキー