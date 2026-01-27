#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME=${1:-mistral}

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama CLI is not installed. Use docker-compose to run it or install from https://ollama.com" >&2
  exit 1
fi

echo "Pulling model: ${MODEL_NAME}"
ollama pull "${MODEL_NAME}"

echo "Starting ollama server (if not already running)"
OLLAMA_HOST=0.0.0.0 ollama serve &
sleep 2

curl -fsS http://localhost:11434/api/tags >/dev/null && echo "Ollama is running."
