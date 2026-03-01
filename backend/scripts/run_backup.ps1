# BizPilot DB バックアップ実行スクリプト
# Windows タスクスケジューラから呼び出す

$WorkspaceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$BackendDir    = Join-Path $WorkspaceRoot "backend"
$LogDir        = Join-Path $WorkspaceRoot "logs" "backup"
$LogFile       = Join-Path $LogDir "backup_$(Get-Date -Format 'yyyyMM').log"

# ログディレクトリ作成
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

Write-Log "=== バックアップ開始 ==="

# Python 仮想環境を探す
$PythonExe = $null
$VenvPython = Join-Path $BackendDir "venv\Scripts\python.exe"
$WorkspacePython = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
    Write-Log "Python: $VenvPython"
} elseif (Test-Path $WorkspacePython) {
    $PythonExe = $WorkspacePython
    Write-Log "Python: $WorkspacePython"
} else {
    Write-Log "ERROR: Python 仮想環境が見つかりません"
    exit 1
}

# .env ファイルのパスを確認
$EnvFile = Join-Path $BackendDir ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Log "WARNING: .env ファイルが見つかりません: $EnvFile"
    Write-Log "環境変数 DATABASE_URL が直接設定されていることを確認してください"
}

# バックアップスクリプト実行
$ScriptPath = Join-Path $BackendDir "scripts\backup_db.py"
Write-Log "実行: $ScriptPath"

$result = & $PythonExe $ScriptPath 2>&1
$result | ForEach-Object { Write-Log $_ }

if ($LASTEXITCODE -eq 0) {
    Write-Log "=== バックアップ完了 (成功) ==="
} else {
    Write-Log "=== バックアップ失敗 (exitcode=$LASTEXITCODE) ==="
    exit 1
}
