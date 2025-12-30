# Frontend Startup Script
Write-Host "🚀 Starting Suraksh Frontend..." -ForegroundColor Cyan
Write-Host ""

# Fixed: Check if we're in the right directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendPath = Join-Path $scriptPath "frontend"

if (-not (Test-Path $frontendPath)) {
    Write-Host "❌ Error: Frontend directory not found at $frontendPath" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

Set-Location $frontendPath

# Fixed: Check if node_modules exists (dependencies installed)
if (-not (Test-Path "node_modules")) {
    Write-Host "⚠️  Dependencies not installed. Installing now..." -ForegroundColor Yellow
    Write-Host ""
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# Fixed: Check if port 3000 is already in use
try {
    $connection = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($connection) {
        Write-Host "⚠️  Port 3000 is already in use. Another process may be running." -ForegroundColor Yellow
        Write-Host "   If you want to start a new instance, please stop the existing one first." -ForegroundColor Yellow
        Write-Host ""
    }
} catch {
    # Port is free, continue
}

Write-Host "✅ Starting Next.js development server..." -ForegroundColor Green
Write-Host "   Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   Login page: http://localhost:3000/auth/login" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the dev server
npm run dev

