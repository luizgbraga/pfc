#!/bin/bash

export NEO4J_URI="bolt://localhost:7689"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="pfcime2025"
export OLLAMA_HOST="http://localhost:11434"

python main.py "$@" 