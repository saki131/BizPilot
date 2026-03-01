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

## デプロイ方法

### Staging環境へのデプロイ
```bash
# backendディレクトリから実行
cd backend
flyctl deploy --config fly.staging.toml
```

- **アプリ名**: bizpilot-backend-staging
- **設定ファイル**: fly.staging.toml
- **リージョン**: San Jose (sjc)
- **メモリ**: 512MB

### 本番環境へのデプロイ
```bash
cd backend
flyctl deploy
```

- **設定ファイル**: fly.toml（デフォルト）

### デプロイ前の確認事項
- Fly.ioにログイン済みか確認: `flyctl auth whoami`
- 環境変数が設定されているか確認: `flyctl secrets list -a bizpilot-backend-staging`
- 必要なシークレット設定: `flyctl secrets set DATABASE_URL=... SECRET_KEY=... -a bizpilot-backend-staging`

## 環境変数
必要に応じて以下の環境変数を設定してください：
- `DATABASE_URL`: PostgreSQL接続文字列
- `SECRET_KEY`: JWTシークレットキー

## DBバックアップ設定

### バックアップ構成
- **スクリプト**: `backend/scripts/backup_db.py`
- **保存先**: Google Drive（サービスアカウント経由）+ ローカル `backend/data/backups/`
- **スケジュール**: Windows タスクスケジューラで毎日 02:00 実行
- **世代管理**: ローカル 7 世代 / Google Drive 30 世代

### セットアップ手順

#### 1. 必要パッケージのインストール
```bash
cd backend
pip install google-api-python-client google-auth psycopg2-binary
```

#### 2. Google Drive サービスアカウントの作成
1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを開く（または新規作成）
2. **APIとサービス** → **ライブラリ** → "Google Drive API" を有効化
3. **APIとサービス** → **認証情報** → **サービスアカウントを作成**
4. サービスアカウントのキーを JSON 形式でダウンロード
5. ダウンロードした JSON を `backend/service_account.json` として保存  
   ⚠️ `.gitignore` に追加して Git にコミットしないこと

#### 3. Google Drive フォルダの共有設定
1. Google Drive でバックアップ用フォルダを作成（例: `BizPilot Backups`）
2. フォルダを右クリック → **共有** → サービスアカウントのメールアドレスを「編集者」で追加
3. フォルダのURLの末尾部分（`/folders/` 以降）をコピー → `GDRIVE_FOLDER_ID` に設定

#### 4. 環境変数の追加（backend/.env）
```env
# Google Drive バックアップ設定
GDRIVE_FOLDER_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GDRIVE_SERVICE_ACCOUNT_JSON=service_account.json
BACKUP_KEEP_GENERATIONS=7
GDRIVE_KEEP_GENERATIONS=30
```

#### 5. 手動テスト
```bash
cd backend
python scripts/backup_db.py
```

#### 6. タスクスケジューラへの登録（毎日 02:00 自動実行）
```powershell
# 管理者権限の PowerShell で実行
cd backend\scripts
.\setup_backup_task.ps1
```

#### 7. タスクの動作確認
```powershell
# 即時テスト実行
Start-ScheduledTask -TaskName "BizPilot-DBBackup"

# ログ確認
Get-Content logs\backup\backup_202603.log
```

### 手動バックアップ（緊急時）
```bash
cd backend
python scripts/backup_db.py
```
バックアップファイルは `backend/data/backups/bizpilot_backup_YYYYMMDD_HHMMSS.dump` に保存されます。

### バックアップからの復元
```bash
# pg_restore を使用（.dump 形式）
pg_restore -d "$DATABASE_URL" backend/data/backups/bizpilot_backup_YYYYMMDD_HHMMSS.dump

# SQL 形式（.sql）の場合
psql "$DATABASE_URL" -f backend/data/backups/bizpilot_backup_YYYYMMDD_HHMMSS.sql
```