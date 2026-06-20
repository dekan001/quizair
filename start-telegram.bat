@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo ============================================
echo   QuizAIr - start for Telegram
echo ============================================
echo.
echo [build] frontend...
call npm --prefix frontend run build
if errorlevel 1 goto builderr

echo.
"%~dp0backend\.venv\Scripts\python.exe" "%~dp0serve_telegram.py"
goto end

:builderr
echo.
echo BUILD FAILED - check Node.js / npm.
echo.

:end
pause
