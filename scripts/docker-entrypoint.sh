#!/bin/bash
# Docker entrypoint script that pulls required models before starting the API

set -e

echo "🐳 Starting AI Review API container..."

# Wait for Ollama service to be healthy
echo "⏳ Waiting for Ollama service to be ready..."
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if curl -f -s "${OLLAMA_BASE_URL:-http://ollama:11434}/api/tags" > /dev/null 2>&1; then
        echo "✅ Ollama service is ready"
        break
    fi
    
    echo "  Waiting for Ollama... ($((counter + 1))/${timeout})"
    sleep 2
    counter=$((counter + 1))
done

if [ $counter -eq $timeout ]; then
    echo "❌ Timeout waiting for Ollama service"
    exit 1
fi

# Pull required models
echo "📥 Pulling required models..."
python3 /app/scripts/pull_models.py

# Start the API server
echo "🚀 Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000