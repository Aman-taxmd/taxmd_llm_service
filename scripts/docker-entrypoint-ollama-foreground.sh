#!/usr/bin/env bash
set -uo pipefail  # Removed -e to handle errors manually

echo "🚀 Starting Ollama Docker container (Foreground Mode)..."

# Set default environment variables
export OLLAMA_HOST=${OLLAMA_HOST:-"0.0.0.0:11434"}
export OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-"http://localhost:11434"}

# Function to handle shutdown gracefully
cleanup() {
    echo "🛑 Received shutdown signal..."
    # Ollama will be terminated automatically since it's in foreground
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

echo "Starting Ollama server at $OLLAMA_HOST (foreground mode)..."

# Create a background job to pull models once Ollama is ready
{
    echo "📥 Waiting for Ollama to be ready before pulling models..."
    
    # Wait for Ollama to be ready
    timeout=120
    counter=0
    while ! curl -fsS "$OLLAMA_BASE_URL/api/tags" >/dev/null 2>&1; do
        if [ $counter -ge $timeout ]; then
            echo "⚠️ Ollama readiness check timed out - proceeding without model pulling"
            exit 0
        fi
        echo "Waiting for Ollama API... ($counter/$timeout)"
        sleep 2
        ((counter++))
    done

    echo "✅ Ollama is ready! Starting model pull..."
    
    # Pull models using the existing script
    if [ -f "/app/scripts/pull_models.sh" ]; then
        bash /app/scripts/pull_models.sh || {
            echo "⚠️ Model pulling failed, but continuing..."
        }
    else
        echo "⚠️ pull_models.sh not found, skipping model pulling"
    fi
    
    echo "🎉 Model pulling completed!"
} &

MODEL_PULL_JOB=$!
echo "Model pulling job started in background (PID: $MODEL_PULL_JOB)"

echo "🎉 Starting Ollama in foreground mode..."
echo "Container will stay alive as long as Ollama is running"

# Run Ollama in foreground - this will keep the container alive
exec ollama serve