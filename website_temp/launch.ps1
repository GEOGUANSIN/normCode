# Launch NormCode Coming Soon Website
Write-Host "🚀 Starting NormCode Coming Soon website..." -ForegroundColor Cyan
Write-Host ""

$indexPath = Join-Path $PSScriptRoot "index.html"

if (Test-Path $indexPath) {
    Write-Host "✓ Opening in your default browser..." -ForegroundColor Green
    Start-Process $indexPath
    Write-Host ""
    Write-Host "✓ Website opened successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Note: This is a simple static HTML file." -ForegroundColor Yellow
    Write-Host "For a local server, you can use:" -ForegroundColor Yellow
    Write-Host "  - Python: python -m http.server 8000" -ForegroundColor Gray
    Write-Host "  - Node.js: npx serve ." -ForegroundColor Gray
} else {
    Write-Host "✗ Error: index.html not found!" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

