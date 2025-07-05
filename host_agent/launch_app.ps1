# NormCode App Launcher
# This script launches both the frontend and backend services

param(
    [switch]$InstallDeps,
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

Write-Host "NormCode App Launcher" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Function to install dependencies
function Install-Dependencies {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    
    # Check if Python is installed
    if (-not (Test-Command "python")) {
        Write-Host "Python is not installed or not in PATH" -ForegroundColor Red
        Write-Host "Please install Python from https://python.org" -ForegroundColor Red
        exit 1
    }
    
    # Check if Node.js is installed
    if (-not (Test-Command "node")) {
        Write-Host "Node.js is not installed or not in PATH" -ForegroundColor Red
        Write-Host "Please install Node.js from https://nodejs.org" -ForegroundColor Red
        exit 1
    }
    
    # Install Python dependencies
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    Set-Location "app/backend"
    python -m pip install -r ../../requirements.txt
    Set-Location "../.."
    
    # Install Node.js dependencies
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
    Set-Location "app/frontend"
    npm install
    Set-Location "../.."
    
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
}

# Function to start backend
function Start-Backend {
    Write-Host "Starting backend server..." -ForegroundColor Blue
    Set-Location "app/backend"
    Start-Process -FilePath "python" -ArgumentList "main_new.py" -WindowStyle Normal
    Set-Location "../.."
    Write-Host "Backend server started on http://localhost:8000" -ForegroundColor Green
}

# Function to start frontend
function Start-Frontend {
    Write-Host "Starting frontend server..." -ForegroundColor Blue
    Set-Location "app/frontend"
    Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WindowStyle Normal
    Set-Location "../.."
    Write-Host "Frontend server started on http://localhost:5173" -ForegroundColor Green
}

# Main execution
try {
    # Install dependencies if requested
    if ($InstallDeps) {
        Install-Dependencies
    }
    
    # Start services based on parameters
    if ($BackendOnly) {
        Start-Backend
    }
    elseif ($FrontendOnly) {
        Start-Frontend
    }
    else {
        # Start both services
        Start-Backend
        Start-Sleep -Seconds 2  # Give backend a moment to start
        Start-Frontend
        
        Write-Host ""
        Write-Host "Both services are starting!" -ForegroundColor Green
        Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
        Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
        Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Press any key to exit..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} 