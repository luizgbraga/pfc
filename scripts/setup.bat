@echo off
setlocal enabledelayedexpansion

echo 🔍 Checking prerequisites...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo docker-compose is not available. Please install Docker Desktop.
    exit /b 1
)

if "%1"=="--rebuild" (
    echo [Rebuild mode] Building Docker images without cache and forcing recreate...
    docker-compose build --no-cache
    docker-compose up -d --force-recreate
) else if not "%1"=="" (
    echo Usage: %0 [--rebuild]
    exit /b 1
) else (
    echo === Setting up UCO in Docker Neo4j ===
    echo 1. Starting Docker containers...
    docker-compose up -d
)

echo 2. Waiting for services to be ready...
timeout /t 30 /nobreak >nul

echo 3. Pulling the LLM model...
for /f "delims=" %%i in ('docker-compose exec app python -c "from config.settings import DEFAULT_OLLAMA_LLM_MODEL; print(DEFAULT_OLLAMA_LLM_MODEL)" 2^>nul') do set MODEL_NAME=%%i
if "!MODEL_NAME!"=="" (
    set MODEL_NAME=deepseek-r1:1.5b-qwen-distill-q8_0
)

echo    Pulling model: !MODEL_NAME!
docker-compose exec ollama ollama pull !MODEL_NAME!
if errorlevel 1 (
    echo Warning: Could not pull model. You might need to wait for Ollama service to be ready.
)

echo 4. Importing UCO ontology...
docker-compose exec app python scripts/import_uco_to_docker.py
if errorlevel 1 (
    echo Warning: UCO import failed. You might need to run this manually later.
)

echo 5. Verifying the setup...
docker-compose exec app python main.py list-key-concepts --limit 5
if errorlevel 1 (
    echo Warning: Setup verification failed. Check the logs for details.
)

echo Setup complete!
echo Summary:
echo    - Neo4j: http://localhost:7474 (neo4j/pfcime2025)
echo    - Ollama: http://localhost:11434
echo    - Available models: !MODEL_NAME!
echo    - Flask server: http://localhost:5001
echo    - Frontend running at http://localhost:5001
echo    - MQ Consumer: running in background (see logs with 'docker-compose logs mq-consumer')
echo       - RabbitMQ UI: http://localhost:15672

pause
