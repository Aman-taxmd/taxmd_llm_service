# Bedrock LLM API - Docker Setup

This repository provides Docker containers for running the Bedrock LLM API with runtime model switching via `.env` file.

## Quick Start

1. **Copy `.env.example` to `.env`**:
   ```bash
   cp .env.example .env
   ```

2. **Configure your `.env` file**:
   ```env
   LLM_FAMILY=claude
   LLM_MODEL=
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   ```

3. **Build and run**:
   ```bash
   docker-compose up --build fastapi
   ```

## Dockerfiles

### `Dockerfile` / `Dockerfile-fastapi`
FastAPI application container that connects to AWS Bedrock.

**Features:**
- Reads `.env` at runtime for model configuration
- Supports switching models without rebuilding
- Lightweight (no GPU, no Ollama dependencies)

**Usage:**
```bash
docker build -f Dockerfile-fastapi -t bedrock-fastapi .
docker run --env-file .env -p 8000:8000 bedrock-fastapi
```

### `Dockerfile-bedrock`
Test/dev container for Bedrock API testing.

**Features:**
- AWS CLI and boto3 pre-installed
- Interactive shell for testing Bedrock connections
- Useful for debugging and manual API calls

**Usage:**
```bash
docker build -f Dockerfile-bedrock -t bedrock-test .
docker run --env-file .env -it bedrock-test
```

## Runtime Model Switching

You can switch models at runtime by updating `.env` and restarting:

```bash
# Edit .env
LLM_FAMILY=llama
LLM_MODEL=meta.llama3-8b-instruct-v1:0

# Restart container
docker-compose restart fastapi
```

The entrypoint script (`scripts/docker-entrypoint-fastapi.sh`) will:
1. Load variables from `.env`
2. Validate AWS credentials
3. Display current configuration
4. Start FastAPI with the selected model

## Available Model Families

- **claude**: Anthropic Claude models
  - Default: `anthropic.claude-3-5-sonnet-20241022-v2:0`
  - Options: `anthropic.claude-3-5-haiku-20241022-v1:0`, `anthropic.claude-3-opus-20240229-v1:0`, etc.

- **llama**: Meta LLaMA models
  - Default: `meta.llama3-8b-instruct-v1:0`
  - Options: `meta.llama3-70b-instruct-v1:0`, `meta.llama3-1-8b-instruct-v1:0`, etc.

- **ministral**: Mistral/Ministral models
  - Default: `mistral.mistral-small-2402-v1:0`
  - Options: `mistral.mistral-large-2402-v1:0`, `mistral.mixtral-8x7b-instruct-v0:1`, etc.

- **titan**: Amazon Titan models
  - Default: `amazon.titan-text-express-v1`
  - Options: `amazon.titan-text-lite-v1`, `amazon.titan-text-premier-v1:0`

## Docker Compose

```bash
# Start FastAPI service
docker-compose up fastapi

# Start with Bedrock test container (interactive)
docker-compose --profile test up bedrock-test

# View logs
docker-compose logs -f fastapi

# Restart after .env changes
docker-compose restart fastapi
```

## Environment Variables

All configuration is done via `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_FAMILY` | Model family (claude, llama, ministral, titan) | `claude` |
| `LLM_MODEL` | Specific model ID (optional, uses family default if empty) | - |
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - |
| `BEDROCK_TIMEOUT` | Request timeout (seconds) | `120` |
| `LLM_MAX_TOKENS` | Max tokens per request | - |
| `LLM_TEMPERATURE` | Temperature (0.0-2.0) | - |
| `LLM_STREAMING` | Enable streaming responses | `true` |
| `LOG_LEVEL` | Logging level | `info` |
| `PORT` | API port | `8000` |

## Entrypoint Scripts

- **`scripts/docker-entrypoint-fastapi.sh`**: Main FastAPI entrypoint
  - Loads `.env` at startup
  - Validates AWS credentials
  - Tests Bedrock connection
  - Starts uvicorn server

- **`scripts/docker-entrypoint-bedrock.sh`**: Bedrock test container entrypoint
  - Loads `.env`
  - Provides interactive shell
  - Shows configuration summary

## Testing Different Models

1. **Via .env file**:
   ```bash
   # Switch to LLaMA
   echo "LLM_FAMILY=llama" >> .env
   echo "LLM_MODEL=meta.llama3-70b-instruct-v1:0" >> .env
   docker-compose restart fastapi
   ```

2. **Via docker-compose override**:
   ```bash
   docker-compose run --rm -e LLM_FAMILY=ministral -e LLM_MODEL=mistral.mixtral-8x7b-instruct-v0:1 fastapi
   ```

3. **Via API request** (if model parameter is supported):
   ```bash
   curl -X POST http://localhost:8000/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"messages": [{"role": "user", "content": "Hello"}], "model": "anthropic.claude-3-5-haiku-20241022-v1:0"}'
   ```
