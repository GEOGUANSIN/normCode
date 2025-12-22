# Setup script for Normcode Editor Frontend
# Run this script from the frontend directory

Write-Host "Setting up Normcode Editor Frontend..." -ForegroundColor Green

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check if npm is available
try {
    $npmVersion = npm --version
    Write-Host "npm version: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "npm is not available. Please install npm." -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "Failed to install dependencies." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Setup complete! To start the development server, run:" -ForegroundColor Green
Write-Host "npm run dev" -ForegroundColor Cyan
Write-Host ""
Write-Host "The frontend will be available at http://localhost:3000" -ForegroundColor Cyan
Write-Host "Make sure the backend is running on http://127.0.0.1:8001" -ForegroundColor Cyan
