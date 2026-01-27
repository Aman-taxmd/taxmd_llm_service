#!/bin/bash
# Optimized preload for phi4 model on 8GB GPU

echo "🚀 Optimizing phi4 model for 8GB GPU..."

# Wait for ollama to be ready
until curl -s http://localhost:11434/api/tags > /dev/null; do
  echo "Waiting for ollama..."
  sleep 2
done

echo "📊 Current GPU memory:"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader,nounits

echo "⚡ Configuring phi4 for hybrid GPU/CPU inference..."

# Preload with optimized settings for 8GB GPU
curl -s -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi4",
    "messages": [{"role": "user", "content": "Ready"}],
    "options": {
      "num_gpu": 1,
      "gpu_layers": 25,
      "batch_size": 256,
      "num_ctx": 1024,
      "num_thread": 8,
      "temperature": 0.3,
      "top_k": 8,
      "top_p": 0.7,
      "repeat_penalty": 1.05,
      "num_predict": 3
    },
    "keep_alive": "60m"
  }' > /dev/null

echo "📊 GPU memory after optimization:"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader,nounits

echo "✅ phi4 optimized and ready for fast inference!"