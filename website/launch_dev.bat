@echo off
REM ============================================
REM NormCode Website Dev Server Launcher
REM ============================================
echo.
echo ========================================
echo    NormCode Website - Dev Mode
echo ========================================
echo.
echo Starting development server...
echo.

cd /d "%~dp0"
npm run dev

pause

