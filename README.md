# Cyber Security Playbook Generator

A tool for generating cyber security playbooks using Neo4j and Ollama.

## Requirements
- Git and Docker
- ~3.8GB RAM free to run tinyllama (default)

## Quick Start

```bash
# Clone the repository
https://github.com/luizgbraga/pfc.git

# Make the setup executable
chmod +x ./scripts/setup.sh

# Setup all containers and local LLMs
./scripts/setup.sh
```

## Running Commands

```bash
# Make the script executable (only needed once)
chmod +x ./scripts/run.sh

# Run any command
./run.sh <command> [options]
```

## Available Commands

- `test-neo4j-connection`: Testa a conexão com o Neo4j
- `explore-ontology`: Explora a ontologia UCO
- `list-key-concepts`: Lista os principais conceitos
- `list-relationship-types`: Lista os tipos de relacionamento
- `analyze-ontology`: Fornece uma análise da ontologia
- `list-observables`: Lista observáveis da UCO
- `generate-playbook`: Gera um playbook a partir de um alerta
- `export-playbook`: Exporta um playbook para HTML
- `display-playbook`: Exibe um playbook no terminal

## Stopping the Services

```bash
# Stop services
docker-compose down

# Stop and remove all data
docker-compose down -v
```
