#!/usr/bin/env bash
set -uo pipefail

echo "🔧 Bedrock Test/Dev Container"
echo "=============================="

# Load environment variables from .env if it exists
if [ -f "/app/.env" ]; then
    echo "📄 Loading environment variables from .env file..."
    set -a
    source /app/.env
    set +a
fi

# Set defaults
export AWS_REGION=${AWS_REGION:-"us-east-1"}
export LLM_FAMILY=${LLM_FAMILY:-"claude"}
export LLM_MODEL=${LLM_MODEL:-""}

echo ""
echo "📋 Current Configuration:"
echo "  AWS_REGION: $AWS_REGION"
echo "  LLM_FAMILY: $LLM_FAMILY"
echo "  LLM_MODEL: ${LLM_MODEL:-"(default)"}"
echo ""

# Check AWS credentials
if [ -z "${AWS_ACCESS_KEY_ID:-}" ] && [ -z "${AWS_SECRET_ACCESS_KEY:-}" ]; then
    echo "⚠️  Warning: AWS credentials not set"
    echo "   Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to test Bedrock"
else
    echo "✅ AWS credentials configured"
fi

echo ""
echo "💡 Usage examples:"
echo "  # Test Bedrock connection"
echo "  aws bedrock-runtime list-foundation-models --region $AWS_REGION"
echo ""
echo "  # Test a model invocation (Python)"
echo "  python3 -c \"import boto3; client = boto3.client('bedrock-runtime', region_name='$AWS_REGION'); print('Connected!')\""
echo ""

# Start interactive shell
exec /bin/bash
