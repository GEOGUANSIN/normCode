@echo off
REM NormCode App Launcher (Batch Version)
REM This script launches both the frontend and backend services

echo 🚀 NormCode App Launcher
echo =========================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

REM Start backend
echo 🔧 Starting backend server...
cd app\backend
start "Backend Server" python main_new.py
cd ..\..

REM Wait a moment for backend to start
timeout /t 2 /nobreak >nul

REM Start frontend
echo 🎨 Starting frontend server...
cd app\frontend
start "Frontend Server" npm run dev
cd ..\..

echo.
echo 🎉 Both services are starting!
echo 📱 Frontend: http://localhost:5173
echo 🔧 Backend:  http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit...
pause >nul 