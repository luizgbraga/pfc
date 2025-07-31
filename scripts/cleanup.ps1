#!/usr/bin/env pwsh

Write-Host "This will delete ALL data in your Neo4j database!"
Write-Host "Press Ctrl+C to abort or wait 5 seconds to continue..."
Start-Sleep -Seconds 5

Write-Host "Deleting all nodes and relationships in Neo4j..."
docker-compose exec neo4j cypher-shell -u neo4j -p pfcime2025 "MATCH (n) DETACH DELETE n"

Write-Host "Cleanup complete. The database is now empty."