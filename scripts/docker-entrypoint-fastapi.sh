#!/usr/bin/env bash
set -uo pipefail

echo "🚀 Starting FastAPI Bedrock LLM API container..."

# Function to handle shutdown gracefully
cleanup() {
    echo "🛑 Received shutdown signal..."
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Load environment variables from .env if it exists
if [ -f "/app/.env" ]; then
    echo "📄 Loading environment variables from .env file..."
    set -a
    source /app/.env
    set +a
fi

# Validate required Bedrock environment variables
echo "🔍 Validating Bedrock configuration..."

# Check LLM_FAMILY (default to claude if not set)
export LLM_FAMILY=${LLM_FAMILY:-"claude"}
echo "  LLM_FAMILY: $LLM_FAMILY"

# Check LLM_MODEL (optional - will use default for family if not set)
if [ -n "${LLM_MODEL:-}" ]; then
    echo "  LLM_MODEL: $LLM_MODEL"
else
    echo "  LLM_MODEL: (using default for $LLM_FAMILY family)"
fi

# Check AWS_REGION
export AWS_REGION=${AWS_REGION:-"us-east-1"}
echo "  AWS_REGION: $AWS_REGION"

# Check AWS credentials (can be from env vars, IAM role, or .env file)
if [ -z "${AWS_ACCESS_KEY_ID:-}" ] && [ -z "${AWS_SECRET_ACCESS_KEY:-}" ]; then
    echo "⚠️  Warning: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not set"
    echo "   Assuming IAM role or instance profile credentials"
else
    echo "  AWS credentials: Configured"
fi

# Check other optional settings
export LLM_MAX_TOKENS=${LLM_MAX_TOKENS:-""}
export LLM_TEMPERATURE=${LLM_TEMPERATURE:-""}
export LLM_STREAMING=${LLM_STREAMING:-"true"}
export BEDROCK_TIMEOUT=${BEDROCK_TIMEOUT:-"120"}
export LOG_LEVEL=${LOG_LEVEL:-"info"}
export PORT=${PORT:-"8000"}

echo ""
echo "📋 Configuration Summary:"
echo "  Model Family: $LLM_FAMILY"
echo "  Model: ${LLM_MODEL:-"(default)"}"
echo "  AWS Region: $AWS_REGION"
echo "  Max Tokens: ${LLM_MAX_TOKENS:-"(default)"}"
echo "  Temperature: ${LLM_TEMPERATURE:-"(default)"}"
echo "  Streaming: $LLM_STREAMING"
echo "  Log Level: $LOG_LEVEL"
echo "  Port: $PORT"
echo ""

# Optional: Test Bedrock connection (non-blocking)
echo "🔌 Testing Bedrock connection..."
python3 -c "
import boto3
import os
from botocore.config import Config

try:
    region = os.getenv('AWS_REGION', 'us-east-1')
    config = Config(read_timeout=int(os.getenv('BEDROCK_TIMEOUT', '120')))
    kwargs = {'region_name': region, 'config': config}
    
    if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
        kwargs['aws_access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID')
        kwargs['aws_secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    client = boto3.client('bedrock-runtime', **kwargs)
    print('✅ Bedrock client initialized successfully')
except Exception as e:
    print(f'⚠️  Bedrock client initialization warning: {e}')
    print('   Continuing anyway - credentials may be available at runtime')
" 2>&1 || echo "⚠️  Bedrock connection test skipped"

echo ""
echo "🎉 Starting FastAPI server..."
echo "   You can change models at runtime by updating .env and restarting"
echo ""

# Start FastAPI with uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
