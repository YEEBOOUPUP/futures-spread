@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo ============================================
echo  外盘数据更新：马棕 / 美豆油（读取您的 Excel）
echo ============================================
echo.
echo [1/3] 导入外盘 Excel（请确认 Excel 已关闭，否则会失败）...
python collector\foreign_excel.py
if errorlevel 1 (
    echo.
    echo 导入失败！请确认：Excel 文件未被占用、路径正确。
    pause
    exit /b 1
)
echo.
echo [2/3] 推送到 GitHub ...
git add -A
git commit -m "外盘数据更新 %date% %time%"
git push origin main
echo.
echo [3/3] 完成！网站 1-3 分钟后自动更新
echo.
pause
