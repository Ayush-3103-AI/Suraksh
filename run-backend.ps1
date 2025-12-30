# Simple Backend Startup Script
# Fixes the "uvicorn is not recognized" error

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Suraksh Backend API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to backend directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend"

if (-not (Test-Path $backendDir)) {
    Write-Host "❌ ERROR: backend directory not found!" -ForegroundColor Red
    Write-Host "   Expected: $backendDir" -ForegroundColor Yellow
    exit 1
}

Set-Location $backendDir
Write-Host "📁 Working directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    exit 1
}

# Check if uvicorn is installed
Write-Host "🔍 Checking dependencies..." -ForegroundColor Yellow
python -c "import uvicorn; import fastapi" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Dependencies missing. Installing..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✅ Dependencies OK" -ForegroundColor Green
Write-Host ""

# Display service URLs
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Service URLs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 Backend API:    http://localhost:8000" -ForegroundColor Green
Write-Host "📚 API Docs:       http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host "❤️  Health Check:   http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server using python -m uvicorn (FIXES THE ERROR)
Write-Host "Starting server..." -ForegroundColor Green
Write-Host ""
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

