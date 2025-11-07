# NormCode App Launcher

This directory contains launcher scripts to easily start both the frontend and backend services for the NormCode application.

## Prerequisites

Before using the launcher, make sure you have the following installed:

- **Python 3.8+** - [Download from python.org](https://python.org)
- **Node.js 16+** - [Download from nodejs.org](https://nodejs.org)

## Quick Start

### Option 1: PowerShell Launcher (Recommended)

```powershell
# Launch both frontend and backend
.\launch_app.ps1

# Install dependencies first, then launch
.\launch_app.ps1 -InstallDeps

# Launch only backend
.\launch_app.ps1 -BackendOnly

# Launch only frontend
.\launch_app.ps1 -FrontendOnly
```

### Option 2: Batch File Launcher

```cmd
# Launch both frontend and backend
launch_app.bat
```

## What the Launcher Does

1. **Checks Prerequisites**: Verifies that Python and Node.js are installed
2. **Installs Dependencies** (if `-InstallDeps` flag is used):
   - Installs Python packages from `requirements.txt`
   - Installs Node.js packages from `package.json`
3. **Starts Backend**: Launches the FastAPI server on `http://localhost:8000`
4. **Starts Frontend**: Launches the Vite development server on `http://localhost:5173`

## Access Points

Once launched, you can access:

- **Frontend Application**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Manual Launch (Alternative)

If you prefer to launch services manually:

### Backend
```bash
cd app/backend
python main.py
```

### Frontend
```bash
cd app/frontend
npm install  # First time only
npm run dev
```

## Troubleshooting

### PowerShell Execution Policy
If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Already in Use
If ports 8000 or 5173 are already in use:
- Backend: Change port in `app/backend/main.py` (line 242)
- Frontend: Change port in `app/frontend/vite.config.js` (if it exists)

### Dependencies Issues
If you encounter dependency issues:
```powershell
# Reinstall Python dependencies
cd app/backend
pip install -r ../../requirements.txt

# Reinstall Node.js dependencies
cd ../frontend
npm install
```

## Stopping the Services

- Close the terminal windows that were opened by the launcher
- Or use `Ctrl+C` in each terminal window
- Or use Task Manager to end the Python and Node.js processes 