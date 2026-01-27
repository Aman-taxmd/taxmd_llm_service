#!/bin/bash
# Download and preload DeepSeek R1 reasoning model

set -e

echo "🤖 Setting up DeepSeek R1 14B reasoning model..."

# Wait for ollama to be ready
until curl -s http://localhost:11434/api/tags > /dev/null; do
  echo "⏳ Waiting for Ollama to be ready..."
  sleep 2
done

echo "✅ Ollama is ready"

# Check if model already exists
if curl -s http://localhost:11434/api/tags | jq -r '.models[].name' | grep -q "deepseek-r1:14b"; then
  echo "✅ DeepSeek R1 14B model already downloaded"
else
  echo "📥 Downloading DeepSeek R1 14B model (this may take a while - ~8.9GB)..."
  
  # Pull the model
  curl -X POST http://localhost:11434/api/pull \
    -H "Content-Type: application/json" \
    -d '{"name": "deepseek-r1:14b"}' \
    --no-buffer | while IFS= read -r line; do
    
    # Parse status from JSON
    status=$(echo "$line" | jq -r '.status // empty' 2>/dev/null || echo "")
    
    if [[ "$status" == "pulling manifest" ]]; then
      echo "📋 Pulling manifest..."
    elif [[ "$status" == "success" ]]; then
      echo "✅ Model downloaded successfully!"
      break
    elif [[ "$status" =~ ^pulling ]]; then
      digest=$(echo "$line" | jq -r '.digest // empty' 2>/dev/null || echo "")
      total=$(echo "$line" | jq -r '.total // empty' 2>/dev/null || echo "")
      completed=$(echo "$line" | jq -r '.completed // empty' 2>/dev/null || echo "")
      
      if [[ -n "$total" && -n "$completed" && "$total" != "null" && "$completed" != "null" ]]; then
        percentage=$((completed * 100 / total))
        echo "📥 Downloading: ${percentage}% ($(numfmt --to=iec $completed)/$(numfmt --to=iec $total))"
      fi
    fi
  done
fi

echo "🔄 Preloading DeepSeek R1 model for instant responses..."

# Preload the model with a simple request
curl -s -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1:14b",
    "messages": [{"role": "user", "content": "Hello, please respond with just OK."}],
    "options": {
      "num_ctx": 1024,
      "top_k": 8,
      "top_p": 0.7,
      "repeat_penalty": 1.05,
      "temperature": 0.3,
      "num_thread": 8,
      "num_gpu": 1,
      "gpu_layers": 25,
      "num_batch": 256,
      "num_predict": 5
    },
    "keep_alive": "30m"
  }' > /dev/null

echo "🚀 DeepSeek R1 14B model is ready for use!"
echo "📊 Model info:"
curl -s http://localhost:11434/api/tags | jq '.models[] | select(.name == "deepseek-r1:14b") | {name, size: (.size | tonumber | . / 1024 / 1024 / 1024 | floor * 100 / 100), parameter_size: .details.parameter_size}'