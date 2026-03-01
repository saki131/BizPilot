# -*- coding: utf-8 -*-
"""
DBバックアップスクリプト
- pg_dump でダンプファイルを作成
- Google Drive の指定フォルダにアップロード
- ローカルの古いバックアップを自動削除（デフォルト: 7世代保持）

使い方:
    python backup_db.py

事前準備:
    1. 環境変数 DATABASE_URL を設定（.env ファイルでも可）
    2. Google Drive サービスアカウントのJSONキーを取得
    3. 下記の GOOGLE_DRIVE_* 環境変数を設定

必要パッケージ:
    pip install google-api-python-client google-auth psycopg2-binary python-dotenv
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# .env 読み込み
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# ─── 設定 ─────────────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL")

# Google Drive サービスアカウント JSONキーのパス
GDRIVE_SERVICE_ACCOUNT_JSON = os.getenv(
    "GDRIVE_SERVICE_ACCOUNT_JSON",
    str(Path(__file__).parent.parent / "service_account.json"),  # デフォルトパス
)

# バックアップを格納する Google Drive フォルダID
# （ブラウザでフォルダを開いた際のURL末尾の英数字）
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "")

# ローカルの一時保存先
BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"

# 保持する世代数
KEEP_GENERATIONS = int(os.getenv("BACKUP_KEEP_GENERATIONS", "7"))

# Google Drive 上で保持する世代数
GDRIVE_KEEP_GENERATIONS = int(os.getenv("GDRIVE_KEEP_GENERATIONS", "30"))

# ─── ロギング設定 ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── pg_dump によるバックアップ ────────────────────────────────────────────────

def create_dump(database_url: str, output_path: Path) -> bool:
    """pg_dump でバックアップファイルを作成する。"""
    logger.info(f"pg_dump 開始 → {output_path.name}")

    # pg_dump コマンドを探す
    pg_dump_cmd = _find_pg_dump()
    if pg_dump_cmd is None:
        logger.warning("pg_dump が見つかりません。Python による CSV ダンプにフォールバックします。")
        return _python_dump_fallback(database_url, output_path)

    cmd = [
        pg_dump_cmd,
        "--format=custom",          # バイナリ形式（圧縮・高速復元）
        "--no-password",
        f"--file={output_path}",
        database_url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # バージョン不一致の場合は Python フォールバックへ
        if "バージョン" in result.stderr or "version" in result.stderr.lower():
            logger.warning(
                f"pg_dump バージョン不一致のため Python フォールバックに切り替えます:\n{result.stderr.strip()}"
            )
            return _python_dump_fallback(database_url, output_path)
        logger.error(f"pg_dump 失敗:\n{result.stderr}")
        return False

    size_mb = output_path.stat().st_size / 1024 / 1024
    logger.info(f"ダンプ完了: {size_mb:.2f} MB")
    return True


def _find_pg_dump() -> str | None:
    """pg_dump 実行ファイルのパスを返す。見つからなければ None。"""
    # 一般的な Windows インストールパスも検索
    candidates = [
        "pg_dump",
        r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
    ]
    for cmd in candidates:
        try:
            result = subprocess.run(
                [cmd, "--version"], capture_output=True, timeout=5
            )
            if result.returncode == 0:
                logger.info(f"pg_dump: {cmd}")
                return cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def _python_dump_fallback(database_url: str, output_path: Path) -> bool:
    """
    pg_dump がない場合の代替: psycopg2 で全テーブルを SQL INSERT 形式でエクスポート。
    ファイル拡張子を .sql に変更して保存する。
    """
    try:
        import psycopg2
    except ImportError:
        logger.error("psycopg2 がインストールされていません: pip install psycopg2-binary")
        return False

    sql_path = output_path.with_suffix(".sql")
    try:
        # Neon のコネクションプーラーは options パラメータ不可 → unpooled に切り替え
        unpooled_url = database_url.replace("-pooler.", ".")
        conn = psycopg2.connect(unpooled_url, connect_timeout=30)
        conn.autocommit = False
        cursor = conn.cursor()

        # search_path を明示的に public に設定
        cursor.execute("SET search_path TO public")

        # 全テーブル一覧を取得（alembic管理外のシステムテーブルを除く）
        cursor.execute(
            """
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
              AND tablename != 'alembic_version'
            ORDER BY tablename
            """
        )
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"テーブル数: {len(tables)}")

        with open(sql_path, "w", encoding="utf-8") as f:
            f.write(f"-- BizPilot DB Backup\n-- Date: {datetime.now().isoformat()}\n\n")
            for table in tables:
                try:
                    cursor.execute(f'SELECT * FROM "{table}"')
                    rows = cursor.fetchall()
                    colnames = [desc[0] for desc in cursor.description]

                    f.write(f"\n-- Table: {table} ({len(rows)} rows)\n")
                    for row in rows:
                        values = ", ".join(
                            "NULL" if v is None else f"'{str(v).replace(chr(39), chr(39)*2)}'"
                            for v in row
                        )
                        cols = ", ".join(f'"{c}"' for c in colnames)
                        f.write(f'INSERT INTO "{table}" ({cols}) VALUES ({values});\n')
                except Exception as table_err:
                    logger.warning(f"テーブル {table} のダンプをスキップ: {table_err}")
                    conn.rollback()
                    # search_path を再設定してから続行
                    cursor.execute("SET search_path TO public")
                    continue

        conn.close()

        # 出力パスを SQL ファイルに差し替え
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path != sql_path:
            output_path.unlink(missing_ok=True)

        size_kb = sql_path.stat().st_size / 1024
        logger.info(f"SQL ダンプ完了: {size_kb:.1f} KB → {sql_path.name}")
        return True

    except Exception as e:
        logger.error(f"Python ダンプ失敗: {e}")
        return False


# ─── Google Drive アップロード ─────────────────────────────────────────────────

def upload_to_google_drive(file_path: Path, folder_id: str, service_account_json: str) -> bool:
    """Google Drive の指定フォルダにファイルをアップロードする。
    
    OAuth2 トークンファイルが存在する場合はそちらを優先使用（ユーザーのクォータを使用）。
    初回のみブラウザ認証が必要。
    """
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        logger.error(
            "Google クライアントライブラリがインストールされていません:\n"
            "pip install google-api-python-client google-auth google-auth-oauthlib"
        )
        return False

    if not folder_id:
        logger.error("GDRIVE_FOLDER_ID が設定されていません。")
        return False

    service = _get_drive_service(service_account_json)
    if service is None:
        return False

    try:
        file_metadata = {"name": file_path.name, "parents": [folder_id]}
        media = MediaFileUpload(str(file_path), resumable=True)

        uploaded = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id,name,size")
            .execute()
        )
        size_kb = int(uploaded.get("size", 0)) / 1024
        logger.info(f"Google Drive アップロード完了: {uploaded['name']} ({size_kb:.1f} KB)")

        _cleanup_gdrive_old_backups(service, folder_id, GDRIVE_KEEP_GENERATIONS)
        return True

    except Exception as e:
        logger.error(f"Google Drive アップロード失敗: {e}")
        return False


def _get_drive_service(service_account_json: str):
    """Drive サービスを返す。OAuth2トークン優先、なければブラウザ認証を行う。"""
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        import json
    except ImportError:
        logger.error("pip install google-auth-oauthlib が必要です。")
        return None

    SCOPES = ["https://www.googleapis.com/auth/drive"]
    token_path = Path(service_account_json).parent / "gdrive_token.json"
    oauth_client_path = Path(service_account_json).parent / "gdrive_oauth_client.json"

    creds = None

    # 保存済みトークンを読み込む
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # トークンが無効または期限切れなら更新・再認証
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Google Drive トークンを更新しました。")
            except Exception:
                creds = None

        if not creds:
            if not oauth_client_path.exists():
                logger.error(
                    f"OAuth2 クライアントファイルが見つかりません: {oauth_client_path}\n"
                    "セットアップ手順:\n"
                    "  1. Google Cloud Console → 「APIとサービス」→「認証情報」\n"
                    "  2. 「OAuth 2.0 クライアント ID」を作成（種類: デスクトップアプリ）\n"
                    "  3. JSON をダウンロードして gdrive_oauth_client.json として保存"
                )
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(oauth_client_path), SCOPES)
            creds = flow.run_local_server(port=0)
            logger.info("Google Drive の認証が完了しました。")

        # トークンを保存
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _cleanup_gdrive_old_backups(service, folder_id: str, keep: int):
    """Google Drive 上の古いバックアップファイルを削除する。"""
    try:
        query = f"'{folder_id}' in parents and trashed=false and name contains 'bizpilot_backup_'"
        results = (
            service.files()
            .list(q=query, fields="files(id,name,createdTime)", orderBy="createdTime desc")
            .execute()
        )
        files = results.get("files", [])
        if len(files) > keep:
            for old_file in files[keep:]:
                service.files().delete(fileId=old_file["id"]).execute()
                logger.info(f"Google Drive 古いバックアップ削除: {old_file['name']}")
    except Exception as e:
        logger.warning(f"Google Drive クリーンアップ中にエラー: {e}")


# ─── ローカルの古いバックアップ削除 ───────────────────────────────────────────

def cleanup_local_old_backups(backup_dir: Path, keep: int):
    """ローカルの古いバックアップファイルを削除する（keep世代分残す）。"""
    pattern_files = sorted(
        list(backup_dir.glob("bizpilot_backup_*")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old_file in pattern_files[keep:]:
        old_file.unlink()
        logger.info(f"ローカル古いバックアップ削除: {old_file.name}")


# ─── メイン ───────────────────────────────────────────────────────────────────

def main():
    if not DATABASE_URL:
        logger.error("DATABASE_URL が設定されていません。.env ファイルまたは環境変数を確認してください。")
        sys.exit(1)

    # バックアップ保存ディレクトリを作成
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"bizpilot_backup_{timestamp}.dump"
    backup_path = BACKUP_DIR / backup_filename

    # ── 1. ダンプ作成
    success = create_dump(DATABASE_URL, backup_path)
    if not success:
        logger.error("バックアップ作成に失敗しました。")
        sys.exit(1)

    # フォールバック時は .sql で保存されるため実際のパスを確認
    sql_path = backup_path.with_suffix(".sql")
    if not backup_path.exists() and sql_path.exists():
        backup_path = sql_path

    # ── 2. Google Drive アップロード
    if GDRIVE_FOLDER_ID:
        upload_to_google_drive(backup_path, GDRIVE_FOLDER_ID, GDRIVE_SERVICE_ACCOUNT_JSON)
    else:
        logger.warning(
            "GDRIVE_FOLDER_ID が未設定のため、Google Drive アップロードをスキップしました。\n"
            f"ローカルバックアップのみ: {backup_path}"
        )

    # ── 3. ローカル古いバックアップ削除
    cleanup_local_old_backups(BACKUP_DIR, KEEP_GENERATIONS)

    logger.info("✅ バックアップ完了")


if __name__ == "__main__":
    main()
