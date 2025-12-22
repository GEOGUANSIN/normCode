# NormCode Editor - One-Click Launcher

This directory contains convenient launcher scripts to start the NormCode Editor application with a single command or click.

## 🚀 Quick Start

Choose any of these methods to launch the application:

### Method 1: Python Script (Recommended)
```powershell
python app_launcher.py
```

### Method 2: Windows Batch File
Double-click `launch.bat` or run:
```powershell
.\launch.bat
```

### Method 3: PowerShell Script
Right-click `launch.ps1` and select "Run with PowerShell" or run:
```powershell
.\launch.ps1
```

## ✨ Features

The launcher automatically:
- ✅ Creates a Python virtual environment for the backend (if needed)
- ✅ Installs all backend dependencies (if needed)
- ✅ Installs all frontend dependencies (if needed)
- ✅ Starts the FastAPI backend server on port 8001
- ✅ Starts the React frontend dev server on port 5173
- ✅ Opens your default browser to the application
- ✅ Handles graceful shutdown with Ctrl+C

## 📋 Prerequisites

Make sure you have these installed:
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **npm** - (comes with Node.js)

## 🌐 Access Points

Once launched, you can access:
- **Frontend Application**: http://localhost:5173
- **Backend API**: http://127.0.0.1:8001
- **API Documentation**: http://127.0.0.1:8001/docs

## 🛑 Stopping the Application

Press `Ctrl+C` in the terminal window to stop both servers gracefully.

## 🐛 Troubleshooting

### "Python not found"
- Install Python 3.8+ from [python.org](https://www.python.org/downloads/)
- Make sure Python is added to your PATH during installation

### "Node.js not found" or "npm not found"
- Install Node.js from [nodejs.org](https://nodejs.org/)
- npm comes bundled with Node.js

### Port already in use
- Close any applications using port 8001 (backend) or 5173 (frontend)
- Or modify the ports in `app_launcher.py`:
  - Backend port: Change `"--port", "8001"` to another port
  - Frontend port: Configured in `frontend/vite.config.ts`

### Virtual environment issues
- Delete the `backend/venv` folder and run the launcher again
- It will recreate the virtual environment

### Frontend dependency issues
- Delete the `frontend/node_modules` folder
- Delete `frontend/package-lock.json`
- Run the launcher again to reinstall dependencies

## 📝 Manual Setup

If you prefer to set up manually, see the main [README.md](README.md) for detailed instructions.

## 🎯 What's Running?

The launcher manages two processes:

1. **Backend (FastAPI + uvicorn)**
   - Location: `backend/`
   - Command: `uvicorn main:app --reload --port 8001`
   - Purpose: RESTful API for managing NormCode repositories

2. **Frontend (React + Vite)**
   - Location: `frontend/`
   - Command: `npm run dev`
   - Purpose: Interactive web UI for the editor

Both servers run with hot-reload enabled, so changes to code are automatically reflected.

