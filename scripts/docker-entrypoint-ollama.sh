#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting Ollama Docker container..."

# Set default environment variables
export OLLAMA_HOST=${OLLAMA_HOST:-"0.0.0.0:11434"}
export OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-"http://localhost:11434"}

# Function to handle shutdown gracefully
cleanup() {
    echo "🛑 Shutting down Ollama server..."
    if [ ! -z "${OLLAMA_PID:-}" ] && kill -0 $OLLAMA_PID 2>/dev/null; then
        echo "Terminating Ollama process $OLLAMA_PID"
        kill -TERM $OLLAMA_PID 2>/dev/null || true
        # Give it 5 seconds to shutdown gracefully
        for i in {1..5}; do
            if ! kill -0 $OLLAMA_PID 2>/dev/null; then
                echo "Ollama shutdown gracefully"
                break
            fi
            sleep 1
        done
        # Force kill if still running
        if kill -0 $OLLAMA_PID 2>/dev/null; then
            echo "Force killing Ollama process"
            kill -KILL $OLLAMA_PID 2>/dev/null || true
        fi
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT EXIT

# Start Ollama server in background
echo "Starting Ollama server at $OLLAMA_HOST..."
ollama serve &
OLLAMA_PID=$!
echo "Ollama started with PID: $OLLAMA_PID"

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
timeout=60
counter=0
while ! curl -fsS "$OLLAMA_BASE_URL/api/tags" >/dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Ollama failed to start within $timeout seconds"
        cleanup
        exit 1
    fi
    
    # Check if ollama process is still running
    if ! kill -0 $OLLAMA_PID 2>/dev/null; then
        echo "❌ Ollama process died during startup"
        exit 1
    fi
    
    echo "Waiting for Ollama... ($counter/$timeout)"
    sleep 1
    ((counter++))
done

echo "✅ Ollama is ready!"

# Pull models using the existing script (run in background to not block)
echo "📥 Pulling models..."
if [ -f "/app/scripts/pull_models.sh" ]; then
    bash /app/scripts/pull_models.sh &
    MODEL_PULL_PID=$!
    echo "Model pulling started in background (PID: $MODEL_PULL_PID)"
else
    echo "⚠️ pull_models.sh not found, skipping model pulling"
fi

echo "🎉 Container initialization complete!"
echo "Ollama server is running on $OLLAMA_HOST with PID: $OLLAMA_PID"

# Display current status
echo "Current processes:"
ps aux | grep -E "(ollama|python)" | grep -v grep || echo "No relevant processes found"

echo "Keeping container alive - monitoring Ollama process..."

# Keep the container running - use a more robust monitoring approach
while true; do
    if ! kill -0 $OLLAMA_PID 2>/dev/null; then
        echo "❌ Ollama server stopped unexpectedly at $(date)"
        exit 1
    fi
    
    # Check if Ollama API is still responding
    if ! curl -fsS "$OLLAMA_BASE_URL/api/tags" >/dev/null 2>&1; then
        echo "⚠️ Ollama API not responding at $(date)"
    fi
    
    sleep 5
done