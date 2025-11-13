@echo off
color 0B
title NormCode Website - Launcher Menu

:menu
cls
echo.
echo ========================================================
echo          NORMCODE WEBSITE - LAUNCHER MENU
echo ========================================================
echo.
echo  Choose your preferred launcher:
echo.
echo  [1] GUI Launcher (Silent)     - Cleanest experience
echo  [2] GUI Launcher              - With start/stop controls
echo  [3] Batch Launcher             - Simple console launcher
echo  [4] PowerShell Launcher        - Colored output
echo  [5] Python Launcher            - Cross-platform
echo.
echo  [0] Exit
echo.
echo ========================================================
echo.

set /p choice="Enter your choice (0-5): "

if "%choice%"=="1" goto silent_gui
if "%choice%"=="2" goto gui
if "%choice%"=="3" goto batch
if "%choice%"=="4" goto powershell
if "%choice%"=="5" goto python
if "%choice%"=="0" goto end

echo Invalid choice! Please try again.
timeout /t 2 >nul
goto menu

:silent_gui
echo.
echo Launching Silent GUI Launcher...
start "" "%~dp0launch_dev_gui_silent.vbs"
goto end

:gui
echo.
echo Launching GUI Launcher...
start "" pythonw "%~dp0launch_dev_gui.pyw"
goto end

:batch
echo.
echo Launching Batch Launcher...
call "%~dp0launch_dev.bat"
goto end

:powershell
echo.
echo Launching PowerShell Launcher...
powershell -ExecutionPolicy Bypass -File "%~dp0launch_dev.ps1"
goto end

:python
echo.
echo Launching Python Launcher...
python "%~dp0launch_dev.py"
goto end

:end
echo.
echo Thank you for using NormCode!
timeout /t 2 >nul
exit

