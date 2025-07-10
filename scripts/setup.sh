#!/bin/bash
set -e

check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
}

check_docker_compose() {
    if ! command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose is not available. Please install Docker Desktop."
        exit 1
    fi
}

echo "Checking prerequisites..."
check_docker
check_docker_compose

if [[ "$1" == "--rebuild" ]]; then
    echo "[Rebuild mode] Building Docker images without cache and forcing recreate..."
    docker-compose build --no-cache
    docker-compose up -d --force-recreate
elif [[ -n "$1" && "$1" != "--rebuild" ]]; then
    echo "Usage: $0 [--rebuild]"
    exit 1
else
    echo "=== Setting up UCO in Docker Neo4j ==="
    echo "1. Starting Docker containers..."
    docker-compose up -d
fi

echo "2. Waiting for services to be ready..."
sleep 30

echo "3. Pulling the LLM model..."
MODEL_NAME=$(docker-compose exec app python -c "from config.settings import DEFAULT_OLLAMA_LLM_MODEL; print(DEFAULT_OLLAMA_LLM_MODEL)" 2>/dev/null | tr -d '\r\n')
if [ -z "$MODEL_NAME" ]; then
    MODEL_NAME="deepseek-r1:1.5b-qwen-distill-q8_0"
fi

echo "   Pulling model: $MODEL_NAME"
if ! docker-compose exec ollama ollama pull $MODEL_NAME; then
    echo "Warning: Could not pull model. You might need to wait for Ollama service to be ready."
fi

echo "4. Importing UCO ontology..."
if ! docker-compose exec app python scripts/import_uco_to_docker.py; then
    echo "Warning: UCO import failed. You might need to run this manually later."
fi

echo "5. Verifying the setup..."
if ! docker-compose exec app python main.py list-key-concepts --limit 5; then
    echo "Warning: Setup verification failed. Check the logs for details."
fi

echo "Setup complete!"
echo "Summary:"
echo "   - Neo4j: http://localhost:7474 (neo4j/pfcime2025)"
echo "   - Ollama: http://localhost:11434"
echo "   - Available models: $MODEL_NAME"
echo "   - Flask server: http://localhost:5001"
echo "   - Frontend running at http://localhost:5001"
echo "   - MQ Consumer: running in background (see logs with 'docker-compose logs mq-consumer')"
echo "      - RabbitMQ UI: http://localhost:15672"