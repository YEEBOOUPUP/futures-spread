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

Write-Host '[1/4] 正在采集当日收盘价（国内，openctp）...'
python collector\daily_fetch.py
if ($LASTEXITCODE -ne 0) { Write-Host ''; Write-Host '********** 国内采集失败，请检查上方报错 **********'; Pop-Location; exit 1 }

Write-Host '[2/4] 正在更新外盘收盘价（新浪）...'
python collector\foreign_fill.py
if ($LASTEXITCODE -ne 0) { Write-Host ''; Write-Host '********** 外盘更新失败，请检查上方报错 **********'; Pop-Location; exit 1 }

Write-Host '[3/4] 提交数据 ...'
git add data\index.json data\*.json
git commit -m "Daily data update"

Write-Host '[4/4] 推送到 GitHub ...'
git push
if ($LASTEXITCODE -ne 0) { Write-Host ''; Write-Host '********** 推送失败，请检查上方报错 **********'; Pop-Location; exit 1 }

Write-Host ''
Write-Host '============================================'
Write-Host '  更新完成！1-2 分钟后线上数据更新'
Write-Host '  网址: https://yeebooupup.github.io/futures-spread/'
Write-Host '============================================'
Pop-Location
