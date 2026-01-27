# AI Review Service - Setup and Run Guide

## Overview

The AI Review Service is a production-ready FastAPI application that provides a chat completion API backed by local AI models through Ollama. It supports multiple models (Mistral, DeepSeek), streaming responses, and is designed with tax assistance and code review use cases in mind.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.11+ (tested with 3.12.3)
- **Docker & Docker Compose**: For containerized deployment
- **Ollama**: For running local AI models (optional for API testing)
- **Git**: For version control
- **Curl**: For API testing

### Hardware Requirements
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: 8GB+ (16GB recommended for larger models)
- **Disk**: 10GB+ free space (models can be large)
- **GPU**: Optional but recommended for faster inference (NVIDIA with CUDA support)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/TaxAssistant/ai_review
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env if needed (optional)
   ```

3. **Start Ollama service:**
   ```bash
   docker compose up -d ollama
   ```

4. **Pull AI models:**
   ```bash
   # For Mistral model
   docker exec -it ollama ollama pull mistral
   
   # For DeepSeek model (optional)
   docker exec -it ollama ollama pull deepseek-coder:6.7b
   ```

5. **Start the API service:**
   ```bash
   docker compose up --build -d api
   ```

6. **Verify the service is running:**
   ```bash
   curl http://localhost:8000/
   # Expected: {"status":"ok","service":"mistral-api"}
   ```

### Option 2: Local Development

1. **Set up Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and start Ollama locally:**
   ```bash
   # Install Ollama (visit https://ollama.ai for installation instructions)
   # Or use the init script:
   ./scripts/init_ollama.sh mistral
   ```

4. **Set environment variables:**
   ```bash
   export OLLAMA_BASE_URL=http://localhost:11434
   export DEFAULT_MODEL=mistral
   export LOG_LEVEL=info
   ```

5. **Start the API server:**
   ```bash
   # Using uvicorn directly
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   
   # Or using Make
   make dev
   ```

## 🛠️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API base URL |
| `DEFAULT_MODEL` | `mistral` | Default model to use |
| `LOG_LEVEL` | `info` | Logging level (debug, info, warning, error) |

### Model Configuration

Edit `models.yaml` to configure available models and their aliases:

```yaml
models:
  default:
    provider: ollama
    model_name: mistral
  deepseek:
    provider: ollama
    model_name: deepseek-coder:6.7b
  mistral:
    provider: ollama
    model_name: mistral
```

## 📡 API Endpoints

### Health Checks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root health check |
| `/health/live` | GET | Liveness probe |
| `/health/ready` | GET | Readiness probe (checks Ollama) |

### Chat Completion

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat` | POST | Chat completion endpoint |

#### Request Format:

```json
{
  "model": "mistral",
  "system": "You are a helpful tax assistant",
  "messages": [
    {
      "role": "user",
      "content": "What is the standard deduction for 2024?"
    }
  ],
  "temperature": 0.3,
  "max_tokens": 300,
  "stream": false,
  "options": {
    "top_k": 40,
    "top_p": 0.9
  }
}
```

#### Parameters:
- **model** (string, optional): Model alias from `models.yaml`
- **system** (string, optional): System prompt
- **messages** (array, required): Conversation messages
- **temperature** (float, 0.0-2.0): Sampling temperature
- **max_tokens** (integer): Maximum tokens to generate
- **stream** (boolean): Enable streaming response
- **options** (object, optional): Additional model parameters

## 🧪 Testing the API

### Using Curl

1. **Basic health check:**
   ```bash
   curl -X GET http://localhost:8000/health/ready
   ```

2. **Simple chat request:**
   ```bash
   curl -X POST http://localhost:8000/v1/chat \
     -H "Content-Type: application/json" \
     -d '{
       "model": "mistral",
       "messages": [
         {"role": "user", "content": "Hello! Explain what you are."}
       ],
       "temperature": 0.7,
       "max_tokens": 100
     }'
   ```

3. **Streaming chat request:**
   ```bash
   curl -X POST http://localhost:8000/v1/chat \
     -H "Content-Type: application/json" \
     -d '{
       "model": "mistral",
       "messages": [
         {"role": "user", "content": "Write a comprehensive tax planning guide."}
       ],
       "temperature": 0.3,
       "max_tokens": 500,
       "stream": true
     }'
   ```

### Using Postman

1. **Import the collection:**
   - Import `AI_Review_API_Collection.json` into Postman
   - Set the `baseUrl` variable to `http://localhost:8000`

2. **Available test scenarios:**
   - Health checks (root, liveness, readiness)
   - Basic chat completions
   - Multi-turn conversations
   - Different model testing (Mistral, DeepSeek)
   - Streaming responses
   - Parameter testing (temperature, max_tokens)
   - Tax-specific use cases
   - Code generation and review
   - Error scenarios
   - Performance testing

### Using the Web Interface

Visit `http://localhost:8000/docs` for interactive API documentation powered by FastAPI's built-in Swagger UI.

## 📊 Available Models

### Mistral
- **Model**: `mistral`
- **Use case**: General purpose, tax advice, conversational AI
- **Size**: ~4.1GB
- **Performance**: Fast, efficient for most tasks

### DeepSeek Coder
- **Model**: `deepseek-coder:6.7b`
- **Use case**: Code generation, code review, technical tasks
- **Size**: ~3.8GB
- **Performance**: Excellent for programming tasks

## 🔧 Development

### Code Quality Tools

```bash
# Format code
make fmt

# Run linting
make lint

# Run tests
make test

# Full development server
make dev
```

### Project Structure

```
ai_review/
├── app/
│   ├── api/
│   │   └── routers/
│   │       ├── chat.py      # Chat completion endpoint
│   │       └── health.py    # Health check endpoints
│   ├── core/
│   │   ├── config.py        # Configuration management
│   │   ├── logging.py       # Logging configuration
│   │   └── model_loader.py  # Model configuration loader
│   ├── services/
│   │   ├── mistral_client.py    # Ollama client
│   │   └── provider_registry.py # Model provider registry
│   ├── tests/               # Test files
│   └── main.py             # FastAPI application entry point
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile             # Container build definition
├── models.yaml            # Model configuration
└── requirements.txt       # Python dependencies
```

## 🐳 Docker Commands

### Basic Operations

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Rebuild and start
docker compose up --build -d

# View logs
docker compose logs -f api
docker compose logs -f ollama

# Execute commands in containers
docker exec -it ollama ollama list
docker exec -it mistral-api python -c "import app; print('API is ready')"
```

### GPU Support (NVIDIA)

```bash
# Start with GPU support
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d ollama

# Verify GPU usage
docker exec -it ollama nvidia-smi
```

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Check what's using port 8000
   ss -tlnp | grep :8000
   
   # Change port in docker-compose.yml or use different port
   docker compose up -d -e PORT=8001
   ```

2. **Ollama connection failed:**
   ```bash
   # Check Ollama is running
   curl http://localhost:11434/api/tags
   
   # Check Ollama container logs
   docker compose logs ollama
   ```

3. **Model not found:**
   ```bash
   # List available models
   docker exec -it ollama ollama list
   
   # Pull missing model
   docker exec -it ollama ollama pull mistral
   ```

4. **Out of memory:**
   - Reduce model size or use smaller models
   - Increase Docker memory limits
   - Use GPU if available

5. **Slow responses:**
   - Ensure GPU support is enabled
   - Check system resources (CPU, RAM)
   - Reduce `max_tokens` parameter
   - Use smaller models for testing

### Logs and Debugging

```bash
# API application logs
docker compose logs -f api

# Ollama service logs
docker compose logs -f ollama

# Enable debug logging
export LOG_LEVEL=debug
make dev

# Check health endpoints
curl -v http://localhost:8000/health/ready
```

## 📈 Performance Optimization

### Hardware Optimization
- **GPU**: Use NVIDIA GPU with CUDA for 3-10x speed improvement
- **RAM**: 16GB+ recommended for larger models
- **SSD**: Fast storage improves model loading time

### Configuration Optimization
- **Temperature**: Lower values (0.1-0.3) for factual responses
- **Max tokens**: Limit to required length for faster responses
- **Batch size**: Use smaller batches for lower memory usage

### Production Deployment
- Use Docker in production
- Set up reverse proxy (nginx)
- Configure proper logging and monitoring
- Use environment-specific configurations
- Implement rate limiting
- Set up health checks and auto-restart

## 🔐 Security Considerations

- API runs on local network by default
- No built-in authentication (add reverse proxy with auth)
- Validate all inputs in production
- Monitor resource usage to prevent abuse
- Use HTTPS in production
- Regularly update dependencies

## 🆘 Support and Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- Ollama: https://ollama.ai/
- Pydantic: https://pydantic-docs.helpmanual.io/

### Model Resources
- Mistral: https://mistral.ai/
- DeepSeek: https://www.deepseek.com/

### Getting Help
- Check logs first: `docker compose logs -f`
- Verify configuration: `curl http://localhost:8000/health/ready`
- Review Postman collection for working examples
- Check GitHub issues for common problems

## 📝 Development Workflow

1. **Make changes** to the code
2. **Run tests**: `make test`
3. **Check code quality**: `make lint && make fmt`
4. **Test locally**: `make dev`
5. **Test with Docker**: `docker compose up --build`
6. **Update documentation** as needed

---

*This guide covers the complete setup and operation of the AI Review Service. For additional questions or issues, please refer to the troubleshooting section or check the project's issue tracker.*