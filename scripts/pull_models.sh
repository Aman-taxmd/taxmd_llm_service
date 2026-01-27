#!/bin/bash
# Script to pull required models from models.yaml before starting the API

set -e

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Pulling required models from models.yaml..."

# Check if we're in a Docker container
if [ -f /.dockerenv ]; then
    echo "Running inside Docker container"
    # In Docker, use the container's Ollama URL
    export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
else
    echo "Running on host system"
    # On host, use localhost
    export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
fi

echo "Using Ollama at: $OLLAMA_BASE_URL"

# Run the Python script
python3 "$SCRIPT_DIR/pull_models.py"

echo "✅ Model pulling complete"