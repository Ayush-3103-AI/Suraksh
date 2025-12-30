# Start Both Services
Write-Host "Starting Suraksh Services..." -ForegroundColor Green
Write-Host ""

# Start Backend in new window
Write-Host "Starting Backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-backend.ps1"

# Wait a bit
Start-Sleep -Seconds 3

# Start Frontend in new window
Write-Host "Starting Frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-frontend.ps1"

# Wait for services to start
Write-Host ""
Write-Host "Waiting for services to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Check status
Write-Host ""
Write-Host "=== SERVICE STATUS ===" -ForegroundColor Green
Write-Host ""

$backendOk = $false
$frontendOk = $false

try {
    $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
    Write-Host "✅ Backend:  RUNNING on http://localhost:8000" -ForegroundColor Green
    $backendOk = $true
} catch {
    Write-Host "❌ Backend:  NOT RUNNING" -ForegroundColor Red
}

try {
    $r = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2
    Write-Host "✅ Frontend: RUNNING on http://localhost:3000" -ForegroundColor Green
    $frontendOk = $true
} catch {
    Write-Host "❌ Frontend: NOT RUNNING" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== PREVIEW LINKS ===" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Website:     http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔐 Login Page:  http://localhost:3000/auth/login" -ForegroundColor Cyan
Write-Host "📚 API Docs:    http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host "❤️  Health:      http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test Credentials:" -ForegroundColor Yellow
Write-Host "  Username: test / Password: test (L1)" -ForegroundColor White
Write-Host "  Username: admin / Password: test (L3)" -ForegroundColor White
Write-Host "  Username: analyst / Password: test (L2)" -ForegroundColor White
Write-Host ""

if ($backendOk -and $frontendOk) {
    Write-Host "✅ Both services are running! Open http://localhost:3000 in your browser." -ForegroundColor Green
} else {
    Write-Host "⚠️  Some services may still be starting. Check the PowerShell windows for errors." -ForegroundColor Yellow
}

