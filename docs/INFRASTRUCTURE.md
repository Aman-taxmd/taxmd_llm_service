# AI Review System Infrastructure Documentation

## Overview
The AI Review system is a containerized FastAPI service that provides AI-powered tax document analysis using Mistral models via Ollama.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │───▶│  FastAPI (API)  │───▶│   Ollama LLM    │
│   (Port 8002)   │    │  mistral-api    │    │   (Port 11434)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Device Infrastructure

### Hardware Requirements
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: 8GB minimum, 16GB+ recommended for larger models
- **Storage**: 20GB+ free space for models
- **Network**: Stable internet for model downloads

### Current System Specs
- **Platform**: Linux 6.14.0-29-generic
- **Docker**: Containerized deployment
- **Models**: Mistral (4.4GB), DeepSeek-Coder (3.8GB)

### Performance Configuration

#### Ollama Server Settings
```bash
OLLAMA_KEEP_ALIVE=10m           # Keep models loaded for 10 minutes
OLLAMA_NUM_PARALLEL=2           # Support 2 concurrent requests
OLLAMA_MAX_LOADED_MODELS=2      # Keep 2 models in memory
```

#### Performance Optimization Settings
```bash
OLLAMA_NUM_CTX=1024            # Reduced context window (faster processing)
OLLAMA_TOP_K=20                # Limited token sampling (speed focus)
OLLAMA_TOP_P=0.8               # Focused sampling distribution
OLLAMA_REPEAT_PENALTY=1.05     # Prevent repetition loops
OLLAMA_NUM_THREAD=8            # CPU threads for processing
OLLAMA_NUM_GPU=0               # GPU layers (0 = CPU only)
```

## Container Services

### 1. Ollama Service
- **Image**: `ollama/ollama:latest`
- **Container**: `ollama`
- **Port**: 11434
- **Volume**: Persistent model storage
- **Health Check**: `ollama list` command

### 2. API Service  
- **Build**: Local Dockerfile
- **Container**: `mistral-api`
- **Port**: 8002 (external) → 8000 (internal)
- **Dependencies**: Waits for ollama health check

## Endpoints

### Health Endpoints
- `GET /health/live` - Basic liveness check
- `GET /health/ready` - Readiness + ollama connectivity
- `GET /health/performance` - Current optimization settings

### AI Endpoints
- `POST /v1/chat` - Chat completions (streaming/non-streaming)
- `GET /docs` - OpenAPI documentation

## Performance Optimizations Applied

### 1. Reduced Context Window
- **Setting**: `num_ctx: 1024` (from default 4096)
- **Benefit**: 75% reduction in context processing time

### 2. Optimized Sampling
- **Settings**: `top_k: 20, top_p: 0.8` 
- **Benefit**: Faster token generation, focused sampling

### 3. Model Keep-Alive
- **Setting**: Extended to 10 minutes
- **Benefit**: Avoid model reloading between requests

### 4. Parallel Processing
- **Setting**: `OLLAMA_NUM_PARALLEL=2`
- **Benefit**: Support concurrent requests

### 5. Focused Generation
- **Setting**: `repeat_penalty: 1.05`
- **Benefit**: Prevent repetition loops, faster completion

### 6. CPU Threading
- **Setting**: `num_thread: 8`
- **Benefit**: Better CPU utilization

## Performance Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Response Time | 39s | 6-19s | 50-85% faster |
| Load Time | Variable | ~2.8s | Consistent |
| Eval Speed | Slow | ~15s | Optimized |

## Monitoring

### Timing Information
All API responses include detailed timing:
```json
{
  "timing": {
    "api_duration": "6.15s",
    "total_duration": "6.15s", 
    "load_duration": "2.58s",
    "prompt_eval_duration": "1.78s",
    "eval_duration": "1.80s",
    "timestamp": "2025-09-03 06:16:21 UTC",
    "timestamp_iso": "2025-09-03T06:16:21.173639"
  }
}
```

### Log Monitoring
- **Structured JSON logs** with request tracking
- **HTTP access logs** for all API calls
- **Error tracking** with stack traces

## Deployment

### Quick Start
```bash
# 1. Copy environment config
cp .env.example .env

# 2. Start services
docker compose up --build -d

# 3. Test health
curl http://localhost:8002/health/ready

# 4. Test chat
curl -X POST http://localhost:8002/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Environment Variables
All performance settings are configurable via environment variables - see `.env.example` for full list.

## Troubleshooting

### Common Issues
1. **Slow responses**: Check `num_ctx` and model size
2. **Memory issues**: Reduce `OLLAMA_MAX_LOADED_MODELS`
3. **CPU bottleneck**: Increase `OLLAMA_NUM_THREAD`
4. **Port conflicts**: Change API port in docker-compose.yml

### Performance Tuning
- **For speed**: Lower `num_ctx`, `top_k`, increase `top_p`
- **For quality**: Higher `num_ctx`, `top_k`, lower `temperature`
- **For throughput**: Increase `OLLAMA_NUM_PARALLEL`

## Security Considerations
- **No GPU acceleration** (CPU-only for security)
- **Internal networking** between containers
- **No external model access** (self-hosted)
- **Configurable timeouts** and rate limiting ready

## Future Enhancements
- GPU acceleration support (optional)
- Model quantization for faster inference
- Response caching for common queries
- Load balancing for high availability