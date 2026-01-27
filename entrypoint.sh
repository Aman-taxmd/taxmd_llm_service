#!/bin/sh
ollama serve &
sleep 5  # Optionally, poll for readiness instead of sleep
ollama pull llama3.2
ollama pull mistral
wait -n
