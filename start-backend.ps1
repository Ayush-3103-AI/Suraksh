# Backend Startup Script
Write-Host "Starting Suraksh Backend API..." -ForegroundColor Cyan

# Check if Docker services are running
Write-Host "Checking Docker services..." -ForegroundColor Yellow
$servicesRunning = docker compose ps --services --filter "status=running" 2>&1
if ($LASTEXITCODE -ne 0 -or $servicesRunning -notmatch "neo4j|qdrant|minio") {
    Write-Host "⚠️  WARNING: Docker services may not be running!" -ForegroundColor Yellow
    Write-Host "   Run 'docker compose up -d postgres redis neo4j qdrant minio' first" -ForegroundColor Yellow
    Write-Host ""
}

# Navigate to backend directory
if (Test-Path "backend") {
    Set-Location backend
} else {
    Write-Host "❌ ERROR: backend directory not found!" -ForegroundColor Red
    Write-Host "   Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# Start the server using python -m uvicorn (works even if uvicorn is not in PATH)
Write-Host "🚀 Starting backend server on http://localhost:8000" -ForegroundColor Green
Write-Host "📚 API Docs will be available at http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host ""
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

