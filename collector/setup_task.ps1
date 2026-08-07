# -*- coding: utf-8 -*-
# 注册 Windows 计划任务：每个交易日 16:00 自动采集并推送
# 用法：powershell -ExecutionPolicy Bypass -File collector\setup_task.ps1
$bat = Join-Path $PSScriptRoot 'update_daily.bat'
schtasks /create /tn "FuturesSpreadDailyUpdate" /tr "`"$bat`"" /sc daily /st 16:00 /f

if ($LASTEXITCODE -eq 0) {
    Write-Host '计划任务已注册：FuturesSpreadDailyUpdate（每天 16:00 自动采集+推送）'
    Write-Host '验证：schtasks /query /tn FuturesSpreadDailyUpdate'
    Write-Host '删除：schtasks /delete /tn FuturesSpreadDailyUpdate /f'
} else {
    Write-Host '注册失败，请以管理员身份运行 PowerShell 重试'
}
