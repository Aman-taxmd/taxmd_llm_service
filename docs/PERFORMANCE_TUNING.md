# Performance Tuning Guide

## Quick Performance Fixes

### 1. Aggressive Speed Settings (Current)
```bash
# .env configuration for maximum speed
OLLAMA_NUM_CTX=1024          # Smaller context = faster processing
OLLAMA_TOP_K=20              # Limited sampling for speed
OLLAMA_TOP_P=0.8             # Focused probability distribution
OLLAMA_REPEAT_PENALTY=1.05   # Minimal repetition penalty
OLLAMA_NUM_THREAD=8          # Use all available CPU cores
```

### 2. Model-Specific Optimizations

#### For Tax Document Analysis
```bash
# Optimal for short, focused responses
OLLAMA_NUM_CTX=512           # Very small context for simple queries
OLLAMA_TOP_K=10              # Highly focused sampling
OLLAMA_TOP_P=0.7             # Conservative probability
```

#### For Complex Analysis
```bash
# Balance between speed and quality
OLLAMA_NUM_CTX=2048          # Larger context for complex documents
OLLAMA_TOP_K=40              # More sampling options
OLLAMA_TOP_P=0.9             # Broader probability distribution
```

## Hardware Acceleration Options

### CPU Optimization
```bash
# Maximize CPU usage
OLLAMA_NUM_THREAD=16         # Use all CPU cores
OLLAMA_NUM_PARALLEL=4        # More concurrent requests
```

### GPU Acceleration (Optional)
```yaml
# docker-compose.gpu.yml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - OLLAMA_NUM_GPU=1       # Use GPU acceleration
```

## Response Time Targets

| Use Case | Target Time | Configuration |
|----------|-------------|---------------|
| Simple Q&A | 2-5s | num_ctx=512, top_k=10 |
| Tax Analysis | 5-10s | num_ctx=1024, top_k=20 |
| Document Review | 10-20s | num_ctx=2048, top_k=40 |

## Benchmark Results

### Current Performance (CPU-only)
```json
{
  "simple_query": {
    "avg_response_time": "6.15s",
    "load_time": "2.58s",
    "generation_time": "1.80s"
  },
  "complex_query": {
    "avg_response_time": "19.19s", 
    "load_time": "2.83s",
    "generation_time": "15.15s"
  }
}
```

### Optimization Impact
- **84% improvement** from baseline (39s → 6s for simple queries)
- **Consistent load times** (~2.8s with keep-alive)
- **Predictable performance** with proper configuration

## Monitoring Commands

### Check Model Performance
```bash
# Test simple query performance
time curl -X POST http://localhost:8002/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 20}'
```

### Monitor System Resources
```bash
# Check container resource usage
docker stats --no-stream

# Check ollama model status
docker exec ollama ollama list
```

### Performance Endpoint
```bash
# Get current optimization settings
curl http://localhost:8002/health/performance | jq
```

## Troubleshooting Slow Performance

### Diagnosis Steps
1. **Check model loading**: First request after restart will be slower
2. **Monitor CPU usage**: Should be near 100% during generation
3. **Check context size**: Large contexts significantly slow processing
4. **Verify keep-alive**: Models should stay loaded between requests

### Common Fixes
```bash
# Restart with optimized settings
docker compose down
docker compose up --build -d

# Clear model cache if needed
docker volume rm ai_review_ollama
```

## Environment-Specific Tuning

### Development
```bash
OLLAMA_NUM_CTX=512           # Fast feedback
OLLAMA_KEEP_ALIVE=5m         # Quick testing
```

### Production
```bash
OLLAMA_NUM_CTX=1024          # Balanced performance
OLLAMA_KEEP_ALIVE=30m        # Longer model retention
OLLAMA_NUM_PARALLEL=4        # Handle load
```

### High-Performance
```bash
OLLAMA_NUM_CTX=2048          # Quality processing
OLLAMA_NUM_THREAD=16         # Max CPU utilization
OLLAMA_NUM_GPU=1             # GPU acceleration
```