# 每日数据采集 + 推送（openctp 收盘价）
$ErrorActionPreference = 'Continue'

# 兜底 PATH（计划任务环境可能缺）
$env:Path += ';C:\Program Files\Git\cmd;C:\Program Files (x86)\Git\cmd'

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location (Join-Path $dir '..')

# 定位 Python（避免 WindowsApps 占位程序）
$PY = $null
foreach ($cand in @(
  'C:\Users\10172\AppData\Local\Python\bin\python.exe',
  'C:\Users\10172\AppData\Local\Python\pythoncore-3.14-64\python.exe',
  'C:\Python313\python.exe',
  'C:\Python312\python.exe'
)) { if (-not $PY -and (Test-Path $cand)) { $PY = $cand } }
if (-not $PY) { $PY = 'python' }
Write-Host "  Python: $PY" 

Write-Host '============================================'
Write-Host '  每日数据采集（OpenCTP 收盘价）'
Write-Host '============================================'
Write-Host ''

Write-Host '[1/4] 正在采集当日收盘价（国内，openctp）...'
& $PY collector\daily_fetch.py
if ($LASTEXITCODE -ne 0) { Write-Host ''; Write-Host '********** 国内采集失败，请检查上方报错 **********'; Pop-Location; exit 1 }

Write-Host '[2/4] 正在采集持仓龙虎榜（新浪）...'
& $PY collector\rank_fetch.py
if ($LASTEXITCODE -ne 0) { Write-Host ''; Write-Host '********** 龙虎榜采集失败（不阻断） **********' }

Write-Host '[3/4] 提交数据 ...'
git add data\index.json data\*.json data\rank\*.json
git commit -m "Daily data update"

Write-Host '[4/4] 推送到 GitHub ...'
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
