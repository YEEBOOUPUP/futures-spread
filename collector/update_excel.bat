@echo off
set "PATH=%PATH%;C:\Program Files\Git\cmd"
cd /d "%~dp0.."
echo ============================================
echo    Excel 数据更新（油脂油料数据库.xlsx）
echo   [1/3] 外盘：马棕 / 美豆油
echo   [2/3] 菜籽：加菜籽 / 欧菜籽
echo   [3/4] 日度海外数据（国际油脂油料价差）
echo   [4/4] 汇率（棕榈油内外套）
echo   完成后自动推送到 GitHub，网站 1-3 分钟更新
echo ============================================
echo.
echo  请确认 Excel 已关闭，否则该步会失败并自动跳过！
echo.

echo [1/4] 外盘：马棕 / 美豆油 ...
python collector/foreign_excel.py
if errorlevel 1 echo   *** 外盘导入失败（Excel 被占用？），继续后续步骤 ***

echo.
echo [2/4] 菜籽：加菜籽 / 欧菜籽 ...
python tools/extract_canola.py
if errorlevel 1 echo   *** 菜籽提取失败，继续后续步骤 ***

echo.
echo [3/4] 日度海外数据 ...
python tools/extract_profit_flow.py
if errorlevel 1 echo   *** 日度海外数据失败，继续后续步骤 ***

echo.
echo [4/4] 汇率（棕榈油内外套）...
python tools/extract_forex.py
if errorlevel 1 echo   *** 汇率提取失败，继续后续步骤 ***

echo.
echo 推送到 GitHub ...
git add -A
git commit -m "Excel data update %date% %time%"
if errorlevel 1 echo   *** 无数据变化，跳过推送 ***
git push origin main
echo.
echo 完成！网站 1-3 分钟后自动更新
echo.
pause
