# Cyber Security Playbook Generator

A tool for generating cyber security playbooks using Neo4j and Ollama.

## Requirements
- Git and Docker
- ~3.5GB RAM free to run deepseek-r1:1.5b-qwen-distill-q8_0 (default)

## Quick Start

### macOS/Linux
```bash
# Clone the repository
git clone https://github.com/luizgbraga/pfc.git
cd pfc

# Make the setup executable
chmod +x ./scripts/setup.sh

# Setup all containers and local LLMs
./scripts/setup.sh

# Access the UI frontend at
http://localhost:5001
```

### Windows (Command Prompt)
```bash
# Clone the repository
git clone https://github.com/luizgbraga/pfc.git
cd pfc

# Setup all containers and local LLMs
scripts\setup.bat

# Access the UI frontend at
http://localhost:5001
```

### Windows (PowerShell) - Recommended
```bash
# Clone the repository
git clone https://github.com/luizgbraga/pfc.git
cd pfc

# Setup all containers and local LLMs
.\scripts\setup.ps1

# Access the UI frontend at
http://localhost:5001
```

### Rebuild Option
To ignore cache and force rebuild, add the `--rebuild` option:
- **macOS/Linux**: `./scripts/setup.sh --rebuild`
- **Windows (CMD)**: `scripts\setup.bat --rebuild`
- **Windows (PowerShell)**: `.\scripts\setup.ps1 -Rebuild`

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
This will actually send an alert to the server endpoint, which will enqueue it
```bash
curl -X POST http://localhost:5001/generate-playbook \
                                          -H "Content-Type: application/json" \
                                          -d '{"alert":{"alert_name":"Suspicious Login Attempt","incident_type":"Unauthorized Access","severity":"High","source_ip":"192.168.1.100","destination_ip":"10.0.0.5","hostname":"server01","user":"alice","description":"Multiple failed login attempts detected from unusual location.","timestamp":"2024-06-01T12:34:56Z","logs":"Failed password for alice from 192.168.1.100 port 22 ssh2"},"output_file":null,"export":false,"display":true}'
```
It is also possible to run commands directly via terminal:

### macOS/Linux
```bash
# Make the script executable (only needed once)
chmod +x ./scripts/run.sh

# Run any command
./scripts/run.sh <command> [options]
```

### Windows
```bash
# Run any command via Docker directly
docker-compose exec app python main.py <command> [options]
```

## Available Commands

- `test-neo4j-connection`
- `explore-ontology`
- `list-key-concepts`
- `list-relationship-types`
- `analyze-ontology`
- `list-observables`
- `generate-playbook`

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

# See all running containers
docker ps

# See the ontology at
http://localhost:7474/browser/
```
A nice flow of development is to first `curl` the alert into the endpoint and then check the logs of `flask-server` and `mq-consumer`.
