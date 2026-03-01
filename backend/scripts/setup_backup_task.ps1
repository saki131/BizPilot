# Windows タスクスケジューラへのバックアップタスク登録スクリプト
# 管理者権限で実行してください
# 使い方: .\setup_backup_task.ps1

$TaskName    = "BizPilot-DBBackup"
$ScriptPath  = Join-Path $PSScriptRoot "run_backup.ps1"
$Description = "BizPilot データベースの日次バックアップ（毎日 02:00）"

# 既存タスクを削除
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "既存タスクを削除しました。"
}

# アクション: powershell.exe で run_backup.ps1 を実行
$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"$ScriptPath`""

# トリガー: 毎日 02:00
$Trigger = New-ScheduledTaskTrigger -Daily -At "02:00"

# 設定: 失敗時に3回リトライ（5分間隔）
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# タスク登録（現在のユーザーで実行）
Register-ScheduledTask `
    -TaskName    $TaskName `
    -Action      $Action `
    -Trigger     $Trigger `
    -Settings    $Settings `
    -Description $Description `
    -RunLevel    Highest `
    -Force | Out-Null

Write-Host "✅ タスク登録完了: $TaskName"
Write-Host "   スケジュール: 毎日 02:00"
Write-Host "   スクリプト : $ScriptPath"
Write-Host ""
Write-Host "すぐにテスト実行するには:"
Write-Host "   Start-ScheduledTask -TaskName '$TaskName'"
