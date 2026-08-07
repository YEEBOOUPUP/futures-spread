# 每日数据采集 + 推送（openctp 收盘价）
$ErrorActionPreference = 'Continue'

# 兜底 PATH（计划任务环境可能缺）
$env:Path += ';C:\Program Files\Git\cmd;C:\Program Files (x86)\Git\cmd'

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location (Join-Path $dir '..')

Write-Host '============================================'
Write-Host '  每日数据采集（OpenCTP 收盘价）'
Write-Host '============================================'
Write-Host ''

Write-Host '[1/3] 正在采集当日收盘价（国内，openctp）...'
python collector\daily_fetch.py
if ($LASTEXITCODE -ne 0) { Write-Host ''; Write-Host '********** 国内采集失败，请检查上方报错 **********'; Pop-Location; exit 1 }

Write-Host '[2/3] 提交数据 ...'
git add data\index.json data\*.json
git commit -m "Daily data update"

Write-Host '[3/3] 推送到 GitHub ...'
$pushOk = $false
for ($attempt = 1; $attempt -le 3; $attempt++) {
    git push
    if ($LASTEXITCODE -eq 0) { $pushOk = $true; break }
    Write-Host "推送失败（第 $attempt/3 次），10 秒后重试 ..."
    Start-Sleep -Seconds 10
}
if (-not $pushOk) {
    $log = Join-Path $PSScriptRoot 'push_error.log'
    git push 2>&1 | Out-File -Append -Encoding utf8 $log
    Write-Host ''
    Write-Host "********** 推送失败（3 次重试），详见 $log **********"
    Pop-Location; exit 1
}

Write-Host ''
Write-Host '============================================'
Write-Host '  更新完成！1-2 分钟后线上数据更新'
Write-Host '  网址: https://yeebooupup.github.io/futures-spread/'
Write-Host '============================================'
Pop-Location
