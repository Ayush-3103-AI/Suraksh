# Comprehensive Service Startup Script for Suraksh Portal
# This script starts all required services for the Knowledge Graph and RAG chatbot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Suraksh Portal - Service Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "[1/5] Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not found"
    }
    Write-Host "✅ Docker is available: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Docker is not running or not installed!" -ForegroundColor Red
    Write-Host "   Please install Docker Desktop and ensure it's running." -ForegroundColor Yellow
    Write-Host "   Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Start Docker services
Write-Host ""
Write-Host "[2/5] Starting Docker services (PostgreSQL, Redis, Neo4j, Qdrant, MinIO)..." -ForegroundColor Yellow
Write-Host "   This may take a minute on first run..." -ForegroundColor Gray

try {
    # Start services in detached mode
    docker compose up -d postgres redis neo4j qdrant minio
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start Docker services"
    }
    
    Write-Host "✅ Docker services started" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Failed to start Docker services" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Yellow
    exit 1
}

# Wait for services to be ready
Write-Host ""
Write-Host "[3/5] Waiting for services to be ready..." -ForegroundColor Yellow

$maxWait = 60
$waited = 0
$servicesReady = $false

while ($waited -lt $maxWait -and -not $servicesReady) {
    Start-Sleep -Seconds 2
    $waited += 2
    
    # Check if services are responding
    $neo4jReady = $false
    $qdrantReady = $false
    $minioReady = $false
    
    try {
        # Try to check Neo4j container (container name may vary)
        $containers = docker ps --format "{{.Names}}" | Select-String "neo4j"
        if ($containers) { $neo4jReady = $true }
    } catch { }
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:6333/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) { $qdrantReady = $true }
    } catch { }
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9000/minio/health/live" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) { $minioReady = $true }
    } catch { }
    
    if ($neo4jReady -and $qdrantReady -and $minioReady) {
        $servicesReady = $true
    } else {
        Write-Host "   Waiting... ($waited/$maxWait seconds)" -ForegroundColor Gray
    }
}

if ($servicesReady) {
    Write-Host "✅ All services are ready" -ForegroundColor Green
} else {
    Write-Host "⚠️  Services may still be starting (continuing anyway)" -ForegroundColor Yellow
}

# Check Python and dependencies
Write-Host ""
Write-Host "[4/5] Checking Python environment..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "   Please install Python 3.11+ from python.org" -ForegroundColor Yellow
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "backend\app\main.py")) {
    Write-Host "⚠️  WARNING: backend\app\main.py not found" -ForegroundColor Yellow
    Write-Host "   Current directory: $(Get-Location)" -ForegroundColor Gray
    Write-Host "   Switching to project root..." -ForegroundColor Gray
    
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $scriptPath
}

# Install/verify dependencies
Write-Host ""
Write-Host "[5/5] Verifying Python dependencies..." -ForegroundColor Yellow

Set-Location backend

try {
    # Check if uvicorn is installed
    python -c "import uvicorn" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   Installing dependencies (this may take a while)..." -ForegroundColor Gray
        python -m pip install -r requirements.txt --quiet
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install dependencies"
        }
    }
    Write-Host "✅ Dependencies verified" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Failed to verify/install dependencies" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Yellow
    Write-Host "   Try running: python -m pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Display service information
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Service Information" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Neo4j Graph DB:    http://localhost:7474" -ForegroundColor Cyan
Write-Host "   (Browser UI)       Username: neo4j / Password: suraksh_neo4j_pass" -ForegroundColor Gray
Write-Host ""
Write-Host "🔍 Qdrant Vector DB:  http://localhost:6333" -ForegroundColor Cyan
Write-Host "   (Dashboard)        http://localhost:6333/dashboard" -ForegroundColor Gray
Write-Host ""
Write-Host "📦 MinIO Storage:     http://localhost:9001" -ForegroundColor Cyan
Write-Host "   (Console)          Username: minioadmin / Password: minioadmin123" -ForegroundColor Gray
Write-Host ""
Write-Host "🗄️  PostgreSQL:        localhost:5432" -ForegroundColor Cyan
Write-Host "   (Database)         Database: suraksh_db" -ForegroundColor Gray
Write-Host ""
Write-Host "⚡ Redis Cache:        localhost:6379" -ForegroundColor Cyan
Write-Host ""

# Start the backend server
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Backend API Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 Backend will start on: http://localhost:8000" -ForegroundColor Green
Write-Host "📚 API Documentation:     http://localhost:8000/api/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn using python -m (works even if uvicorn is not in PATH)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

