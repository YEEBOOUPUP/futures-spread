# -*- coding: utf-8 -*-
"""生成 GBK 编码的 update_excel.bat（一次性工具，避免 bash/python 转义干扰）"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAT = os.path.join(BASE, 'collector', 'update_excel.bat')

content = r'''@echo off
set "PATH=%PATH%;C:\Program Files\Git\cmd"
cd /d "%~dp0.."
echo ============================================
echo    Excel 数据更新（油脂油料数据库.xlsx）
echo    [1/2] 外盘：马棕 / 美豆油
echo    [2/2] 菜籽：加菜籽 / 欧菜籽
echo    完成后自动推送到 GitHub，网站 1-3 分钟更新
echo ============================================
echo.
echo  请确认 Excel 已关闭，否则会失败！
echo.
echo [1/2] 导入外盘（马棕 / 美豆油）...
python collector/foreign_excel.py
if errorlevel 1 (
    echo.
    echo 外盘导入失败！请确认 Excel 未被占用、路径正确。
    pause
    exit /b 1
)
echo.
echo [2/2] 提取菜籽（加菜籽 / 欧菜籽）...
python tools/extract_canola.py
if errorlevel 1 (
    echo.
    echo 菜籽提取失败！
    pause
    exit /b 1
)
echo.
echo 推送到 GitHub ...
git add -A
git commit -m "Excel data update %date% %time%"
git push origin main
echo.
echo 完成！网站 1-3 分钟后自动更新
echo.
pause
'''

with open(BAT, 'w', encoding='gbk') as f:
    f.write(content)
raw = open(BAT, 'rb').read()
print('已生成 GBK bat:', os.path.basename(BAT))
print('0x0C 坏字节:', raw.count(b'\x0c'))
print('GBK 解码 OK:', bool(raw.decode('gbk')))
print('含 python 路径:', [l for l in raw.decode('gbk').splitlines() if 'python ' in l])
