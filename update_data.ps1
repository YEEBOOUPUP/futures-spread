# 兜底：git 不在 PATH 时补上（Git for Windows 默认安装路径）
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  $candidates = @('C:\Program Files\Git\cmd', 'C:\Program Files (x86)\Git\cmd')
  foreach ($c in $candidates) { if (Test-Path "$c\git.exe") { $env:Path += ';' + $c; break } }
}
$ErrorActionPreference = 'Continue'
Write-Host '============================================'
Write-Host '  期货月差/价差 - 每日数据更新'
Write-Host '============================================'
Write-Host ''

$excel = 'C:\Users\10172\OneDrive\Desktop\临时数据处理\WIND价格-wyb.xlsx'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $dir

Write-Host '[1/3] 正在用最新 Excel 生成 data.json ...'
python tools\excel_to_json.py --input $excel --output data\data.json
if ($LASTEXITCODE -ne 0) { Write-Host ''; Write-Host '********** 生成数据失败，请检查上方报错 **********'; Pop-Location; exit 1 }

Write-Host '[2/3] 提交数据 ...'
git add data\data.json
git commit -m "Daily data update"

Write-Host '[3/3] 推送到 GitHub ...'
git push
if ($LASTEXITCODE -ne 0) { Write-Host ''; Write-Host '********** 推送失败，请检查上方报错 **********'; Pop-Location; exit 1 }

Write-Host ''
Write-Host '============================================'
Write-Host '  更新完成！1-2 分钟后线上数据更新'
Write-Host '  网址: https://yeebooupup.github.io/futures-spread/'
Write-Host '============================================'
Pop-Location