# AI Review Service Documentation

## Overview

The AI Review Service is a FastAPI-based application that provides chat completion capabilities using local AI models via Ollama. It's designed for tax assistance and code review use cases.

## Quick Links

- **[Setup and Installation](SETUP_AND_RUN.md)** - Complete setup guide for local development and Docker deployment
- **[Architecture](ARCHITECTURE.md)** - System architecture and component overview  
- **[Infrastructure](INFRASTRUCTURE.md)** - Infrastructure documentation and deployment details
- **[AWS Deployment](AWS_DEPLOYMENT.md)** - Guide for deploying to AWS
- **[Performance](PERFORMANCE_TUNING.md)** - Performance optimization and tuning guide
- **[GPU Optimization](GPU_OPTIMIZATION.md)** - GPU acceleration setup and optimization

## Features

- ✅ **FastAPI** service with `/v1/chat` endpoint
- ✅ **Ollama** integration for local AI models (Mistral, DeepSeek)
- ✅ **GPU acceleration** support with NVIDIA CUDA
- ✅ **Streaming responses** with NDJSON format
- ✅ **Docker & Docker Compose** for containerized deployment
- ✅ **Model management** via `models.yaml` configuration
- ✅ **Health checks** (liveness/readiness probes)
- ✅ **Production-ready** with proper logging and error handling

## Getting Started

1. **Quick start with Docker:**
   ```bash
   cd ai_review
   docker compose up -d ollama
   docker exec -it ollama ollama pull mistral
   docker compose up --build -d api
   ```

2. **Test the service:**
   ```bash
   curl http://localhost:8000/health/ready
   ```

3. **Make a chat request:**
   ```bash
   curl -X POST http://localhost:8000/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"model": "mistral", "messages": [{"role": "user", "content": "Hello!"}]}'
   ```

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Current Status

- **Service**: ✅ Running on http://localhost:8002 (GPU-optimized)
- **Model**: ✅ Mistral with GPU acceleration (18% GPU, 82% CPU - optimal for this quantized model)
- **GPU**: ✅ NVIDIA RTX 5060 with 500MB VRAM allocated
- **Performance**: ✅ ~15-18 seconds for 150-200 token responses

## Directory Structure

```
ai_review/
├── app/                    # Application source code
│   ├── api/routers/       # API route handlers
│   ├── core/              # Configuration and logging
│   ├── services/          # Business logic and providers
│   └── tests/             # Test files
├── docs/                  # Documentation (this folder)
├── scripts/               # Utility scripts
├── docker-compose.yml     # Docker configuration
├── models.yaml           # Model configuration
└── requirements.txt      # Python dependencies
```

For detailed information, please refer to the specific documentation files listed above.