@echo off
chcp 65001 >nul 2>&1
setlocal
set "SCRIPT_DIR=%~dp0"

echo ==========================================
echo   AI-Content-Automation - STOP ALL
echo ==========================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%stop-all.ps1" %*
set "RC=%ERRORLEVEL%"

endlocal & exit /b %RC%
