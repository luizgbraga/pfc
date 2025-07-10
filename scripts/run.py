#!/usr/bin/env python3
"""
Cross-platform Python script to run commands locally (alternative to run.sh)
This works on Windows, Linux, and macOS without requiring shell permissions
"""
import os
import sys
import subprocess

def main():
    # Set environment variables
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "pfcime2025"
    os.environ["OLLAMA_HOST"] = "http://localhost:11434"
    
    # Pass all arguments to main.py
    args = ["python", "main.py"] + sys.argv[1:]
    
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        sys.exit(1)

if __name__ == "__main__":
    main()
