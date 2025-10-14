# PowerShell script to run Django with WebSocket support
Write-Host "Starting Django with WebSocket support using Daphne..." -ForegroundColor Green
Write-Host ""

# Set Django settings module
$env:DJANGO_SETTINGS_MODULE = "AirplaneDJ.settings"
Write-Host "Setting Django settings module: $env:DJANGO_SETTINGS_MODULE" -ForegroundColor Yellow

Write-Host "Starting Daphne ASGI server on port 8000..." -ForegroundColor Yellow
Write-Host "Access your chat at: http://localhost:8000/chat/" -ForegroundColor Cyan
Write-Host ""

try {
    daphne -p 8000 AirplaneDJ.asgi:application
} catch {
    Write-Host "Error starting server: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure you have daphne installed:" -ForegroundColor Yellow
    Write-Host "pip install daphne" -ForegroundColor White
}

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")