#!/usr/bin/env pwsh

param(
    [switch]$Rebuild
)

function Test-DockerRunning {
    try {
        $null = docker info 2>$null
        return $true
    } catch {
        return $false
    }
}

function Test-DockerCompose {
    try {
        $null = Get-Command docker-compose -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

Write-Host "Checking prerequisites..." -ForegroundColor Cyan

if (-not (Test-DockerRunning)) {
    Write-Host "Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

if (-not (Test-DockerCompose)) {
    Write-Host "docker-compose is not available. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

if ($Rebuild) {
    Write-Host "[Rebuild mode] Building Docker images without cache and forcing recreate..." -ForegroundColor Yellow
    docker-compose build --no-cache
    docker-compose up -d --force-recreate
} else {
    Write-Host "=== Setting up DEF3ND in Docker Neo4j ===" -ForegroundColor Green
    Write-Host "1. Starting Docker containers..." -ForegroundColor Cyan
    docker-compose up -d
}

Write-Host "2. Waiting for services to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

Write-Host "3. Pulling the LLM model..." -ForegroundColor Cyan
try {
    $MODEL_NAME = docker-compose exec app python -c "from config.settings import DEFAULT_OLLAMA_LLM_MODEL; print(DEFAULT_OLLAMA_LLM_MODEL)" 2>$null
    $MODEL_NAME = $MODEL_NAME.Trim()
} catch {
    $MODEL_NAME = ""
}

if ([string]::IsNullOrEmpty($MODEL_NAME)) {
    $MODEL_NAME = "deepseek-r1:1.5b-qwen-distill-q8_0"
}

Write-Host "   Pulling model: $MODEL_NAME" -ForegroundColor Yellow
try {
    docker-compose exec ollama ollama pull $MODEL_NAME
} catch {
    Write-Host "Warning: Could not pull model. You might need to wait for Ollama service to be ready." -ForegroundColor Yellow
}

Write-Host "4. Importing DEF3ND ontology..." -ForegroundColor Cyan
try {
    docker-compose exec app python scripts/import_d3fend_to_docker.py
} catch {
    Write-Host "Warning: DEF3ND import failed. You might need to run this manually later." -ForegroundColor Yellow
}

Write-Host "5. Verifying the setup..." -ForegroundColor Cyan
try {
    docker-compose exec app python main.py list-key-concepts --limit 5
} catch {
    Write-Host "Warning: Setup verification failed. Check the logs for details." -ForegroundColor Yellow
}

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "   - Neo4j: http://localhost:7474 (neo4j/pfcime2025)"
Write-Host "   - Ollama: http://localhost:11434"
Write-Host "   - Available models: $MODEL_NAME"
Write-Host "   - Flask server: http://localhost:5001"
Write-Host "   - Frontend running at http://localhost:5001"
Write-Host "   - MQ Consumer: running in background (see logs with 'docker-compose logs mq-consumer')"
Write-Host "      - RabbitMQ UI: http://localhost:15672"
