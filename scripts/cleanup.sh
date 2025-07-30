#!/bin/bash

set -e

echo "This will delete ALL data in your Neo4j database!"
echo "Press Ctrl+C to abort or wait 5 seconds to continue..."
sleep 5

echo "Deleting all nodes and relationships in Neo4j..."
docker-compose exec neo4j cypher-shell -u neo4j -p pfcime2025 "MATCH (n) DETACH DELETE n"

echo "Cleanup complete. The database is now empty."
