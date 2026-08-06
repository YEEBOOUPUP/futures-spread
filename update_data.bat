@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update_data.ps1"
if errorlevel 1 goto fail
pause
exit /b 0
:fail
echo ********** Update failed, see messages above **********
pause
exit /b 1