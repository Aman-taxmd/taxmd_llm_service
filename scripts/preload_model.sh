#!/bin/bash
# Preload model to eliminate load_duration

echo "Preloading mistral model for instant responses..."

# Wait for ollama to be ready
until curl -s http://localhost:11434/api/tags > /dev/null; do
  echo "Waiting for ollama..."
  sleep 2
done

# Preload the model with a simple request
curl -s -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [{"role": "user", "content": "Hi"}],
    "options": {
      "num_ctx": 512,
      "top_k": 5,
      "top_p": 0.6,
      "temperature": 0.3,
      "num_predict": 1
    },
    "keep_alive": "30m"
  }' > /dev/null

echo "Model preloaded and ready for fast responses!"