#!/usr/bin/env bash
set -euo pipefail

API_BASE=${API_BASE:-http://localhost:8002}
MODEL=${MODEL:-mistral}
STREAM=${STREAM:-false}

echo "🚀 Testing AI Review Chat API"
echo "📍 Base URL: $API_BASE"
echo "🤖 Model: $MODEL"
echo "📡 Stream: $STREAM"
echo "=================================================="

if [ "$STREAM" = "true" ]; then
  echo "🌊 Testing streaming response..."
  curl -N -X POST "$API_BASE/v1/chat" \
    -H 'Content-Type: application/json' \
    -d "$(jq -n --arg model "$MODEL" '{
      model: $model, 
      messages: [{role: "user", content: "Count from 1 to 5, explaining each number"}], 
      temperature: 0.2,
      stream: true,
      max_tokens: 200
    })"
else  
  echo "📦 Testing non-streaming response..."
  curl -sS -X POST "$API_BASE/v1/chat" \
    -H 'Content-Type: application/json' \
    -d "$(jq -n --arg model "$MODEL" '{
      model: $model, 
      messages: [{role: "user", content: "Say hello and introduce yourself briefly"}], 
      temperature: 0.2,
      stream: false,
      max_tokens: 100
    })" | jq .
fi
