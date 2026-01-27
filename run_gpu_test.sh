#!/bin/bash
# GPU-optimized Ollama test script

echo "🚀 Testing GPU-optimized AI inference..."

# Test multiple small requests in parallel to stress GPU
echo "Running parallel GPU stress test..."

start_time=$(date +%s.%N)

# Run 5 parallel requests
for i in {1..5}; do
    curl -s -X POST http://localhost:8002/v1/chat \
        -H "Content-Type: application/json" \
        -d '{
            "model": "mistral",
            "messages": [{"role": "user", "content": "Write a haiku about AI"}],
            "temperature": 0.5,
            "max_tokens": 50
        }' | jq -r '.timing.api_duration' &
done

wait

end_time=$(date +%s.%N)
total_time=$(echo "$end_time - $start_time" | bc)

echo "✅ Parallel test completed in: ${total_time}s"
echo "🔥 Single request performance test:"

# Single optimized request
time curl -s -X POST http://localhost:8002/v1/chat \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mistral", 
        "messages": [{"role": "user", "content": "Explain GPU acceleration in one sentence."}],
        "temperature": 0.3,
        "max_tokens": 30
    }' | jq '.timing'