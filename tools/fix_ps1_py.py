# -*- coding: utf-8 -*-
"""update_daily.ps1 加 Python 路径检测（与 bat 一致）"""
p = 'collector/update_daily.ps1'
c = open(p, encoding='utf-8-sig').read()

old = "Push-Location (Join-Path $dir '..')"
new = old + """

# 定位 Python（避免 WindowsApps 占位程序）
$PY = $null
foreach ($cand in @(
  'C:\\Users\\10172\\AppData\\Local\\Python\\bin\\python.exe',
  'C:\\Users\\10172\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe',
  'C:\\Python313\\python.exe',
  'C:\\Python312\\python.exe'
)) { if (-not $PY -and (Test-Path $cand)) { $PY = $cand } }
if (-not $PY) { $PY = 'python' }
Write-Host "  Python: $PY" """
assert old in c and '定位 Python' not in c, '锚点异常'
c = c.replace(old, new, 1)
c = c.replace('python collector\\daily_fetch.py', '& $PY collector\\daily_fetch.py')
c = c.replace('python collector\\rank_fetch.py', '& $PY collector\\rank_fetch.py')
open(p, 'w', encoding='utf-8-sig').write(c)
raw = open(p, 'rb').read()
txt = raw.decode('utf-8-sig')
print('ps1 已加固 | BOM:', raw[:3] == b'\xef\xbb\xbf')
print('含 PY 检测:', '定位 Python' in txt)
print('daily_fetch/rank_fetch 用 $PY:', '& $PY collector\\daily_fetch.py' in txt, '& $PY collector\\rank_fetch.py' in txt)
