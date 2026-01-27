# Production: single FastAPI + boto3 image. No GPU, no Ollama.
# Bedrock is AWS API only; this container calls it via boto3.
# ONE container = FastAPI + boto3 → AWS Bedrock. Model switch via .env + restart.
# syntax=docker/dockerfile:1.6

FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY pyproject.toml ./
COPY models.yaml ./
COPY scripts ./scripts

# Make scripts executable
RUN chmod +x /app/scripts/*.sh || true

ENV PORT=8000
EXPOSE 8000

# Healthcheck: liveness probe (fast, no external dependencies)
# Uses /health/live endpoint which just checks if service is running
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
  CMD curl -f http://localhost:8000/health/live || exit 1

# Use entrypoint script that reads .env at runtime for model switching
ENTRYPOINT ["/app/scripts/docker-entrypoint-fastapi.sh"]
