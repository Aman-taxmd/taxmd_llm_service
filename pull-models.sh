#!/bin/bash
# Convenience script to pull required models before running docker-compose up

echo "🚀 Pulling required models from models.yaml..."
echo "This ensures all models are available before starting the API."
echo

# Run the model pulling script
./scripts/pull_models.sh

echo
echo "✅ Models are ready! You can now run 'docker-compose up'"
echo