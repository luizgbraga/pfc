# Cyber Security Playbook Generator

A tool for generating cyber security playbooks using Neo4j and Ollama.

## Requirements
- Git and Docker
- ~3.8GB RAM free to run tinyllama (default)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/luizgbraga/pfc.git
cd pfc

# Make the setup executable
chmod +x ./scripts/setup.sh

# Setup all containers and local LLMs
./scripts/setup.sh
```

To ignore cache, add the `--rebuild` option when running `setup.sh`

This will start the following containers:
- **neo4j**: Graph database for storing cybersecurity ontology (UCO) and data (ports 7474, 7687)
- **flask-server**: REST API server with endpoints for generating playbooks (port 5001)
- **mq-consumer**: Message queue consumer for processing alerts, calling the server
- **ollama**: Local LLM service for AI-powered playbook generation (port 11434)
- **rabbitmq**: Message broker for alert processing (ports 5672, 15672)

## Running Commands

This will simulate an alert being sent to the message queue for processing
```bash
# Produce a mock message to the queue
python mq/fake_producer.py
```

It is also possible to run commands directly via terminal
```bash
# Make the script executable (only needed once)
chmod +x ./scripts/run.sh

# Run any command
./scripts/run.sh <command> [options]
```

## Available Commands

- `test-neo4j-connection`
- `explore-ontology`
- `list-key-concepts`
- `list-relationship-types`
- `analyze-ontology`
- `list-observables`
- `generate-playbook`
- `export-playbook`
- `display-playbook`

## Stopping the Services

```bash
# Stop services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Development

```bash
# See the logs of a specific container
docker-compose logs [container-name]
```
