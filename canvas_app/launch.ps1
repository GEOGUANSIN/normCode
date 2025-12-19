# NormCode Canvas - PowerShell Launcher
# Starts both backend and frontend servers

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"
$FrontendDir = Join-Path $ScriptDir "frontend"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting NormCode Canvas" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Check if npm is installed
try {
    $null = Get-Command npm -ErrorAction Stop
} catch {
    Write-Host "Error: npm is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if node_modules exists
if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "`n[Setup] Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location $FrontendDir
    npm install
    Pop-Location
}

Write-Host "`n[1/2] Starting FastAPI backend on http://localhost:8000" -ForegroundColor Green
$backend = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--reload", "--port", "8000" -WorkingDirectory $BackendDir -PassThru -NoNewWindow

Start-Sleep -Seconds 2

Write-Host "`n[2/2] Starting Vite frontend on http://localhost:5173" -ForegroundColor Green
$frontend = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $FrontendDir -PassThru -NoNewWindow

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "NormCode Canvas is running!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`n  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Backend API: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  WebSocket: ws://localhost:8000/ws/events" -ForegroundColor White
Write-Host "`nPress Ctrl+C to stop all servers..." -ForegroundColor Yellow

try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    Write-Host "`nShutting down..." -ForegroundColor Yellow
    
    if (-not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    }
    if (-not $frontend.HasExited) {
        Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "All servers stopped." -ForegroundColor Green
}
