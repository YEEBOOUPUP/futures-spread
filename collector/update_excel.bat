@echo off
set "PATH=%PATH%;C:\Program Files\Git\cmd"
cd /d "%~dp0.."

rem ---- 定位 Python（系统 python 命令可能被 WindowsApps 占位程序拦截）----
set "PY="
for %%P in (
  "C:\Users\10172\AppData\Local\Python\bin\python.exe"
  "C:\Users\10172\AppData\Local\Python\pythoncore-3.14-64\python.exe"
  "C:\Python313\python.exe"
  "C:\Python312\python.exe"
) do (
  if not defined PY if exist %%P set "PY=%%~P"
)
if not defined PY (
  echo.
  echo  未找到 Python！请检查安装路径并修改本脚本中的 PY 候选列表。
  pause
  exit /b 1
)

echo ============================================
echo    Excel 数据更新（油脂油料数据库.xlsx）
echo    [1/4] 外盘：马棕 / 美豆油
echo    [2/4] 菜籽：加菜籽 / 欧菜籽
echo    [3/4] 日度海外数据（国际油脂油料价差）
echo    [4/4] 汇率（棕榈油内外套）
echo    完成后自动推送到 GitHub，网站 1-3 分钟更新
echo ============================================
echo.
echo  Python: %PY%
echo  请确认 Excel 已关闭，否则该步会失败并自动跳过！
echo.

echo [1/4] 外盘：马棕 / 美豆油 ...
"%PY%" collector/foreign_excel.py
if errorlevel 1 echo   *** 外盘导入失败（Excel 被占用？），继续后续步骤 ***

echo.
echo [2/4] 菜籽：加菜籽 / 欧菜籽 ...
"%PY%" tools/extract_canola.py
if errorlevel 1 echo   *** 菜籽提取失败，继续后续步骤 ***

echo.
echo [3/4] 日度海外数据 ...
"%PY%" tools/extract_profit_flow.py
if errorlevel 1 echo   *** 日度海外数据失败，继续后续步骤 ***

echo.
echo [4/4] 汇率（棕榈油内外套）...
"%PY%" tools/extract_forex.py
if errorlevel 1 echo   *** 汇率提取失败，继续后续步骤 ***

echo.
echo 推送到 GitHub ...
git add data
git commit -m "Excel data update %date% %time%"
if errorlevel 1 echo   *** 无数据变化，跳过提交 ***
git -c credential.helper= -c credential.helper=manager push origin main
if errorlevel 1 (
  echo.
  echo   *** 推送失败：请检查网络或 GitHub 登录状态 ***
) else (
  echo.
  echo 完成，网站 1-3 分钟后自动更新
)
echo.
pause
