# NormCode Editor - PowerShell Launcher
# Right-click and select "Run with PowerShell" to launch the application

Write-Host "Starting NormCode Editor..." -ForegroundColor Cyan

python app_launcher.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nPress any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

