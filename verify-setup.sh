#!/bin/bash
# Quick verification script for ai_review project setup

set -e

echo "🔍 AI Review Project - Setup Verification"
echo "=========================================="

# Check Python environment
echo
echo "📋 Checking Python environment..."
if command -v python3 &> /dev/null; then
    echo "✅ Python3 found: $(python3 --version)"
else
    echo "❌ Python3 not found"
    exit 1
fi

# Check virtual environment
echo
echo "📦 Checking virtual environment..."
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found"
    echo "   Run: python3 -m venv venv"
    exit 1
fi

# Check dependencies
echo
echo "🔧 Checking dependencies..."
if python -c "import fastapi, uvicorn, httpx, pydantic, yaml; print('✅ All dependencies available')" 2>/dev/null; then
    echo "✅ Core dependencies installed"
else
    echo "❌ Missing dependencies"
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi

# Check application import
echo
echo "🚀 Checking application..."
if python -c "from app.main import app; print('✅ Application imports successfully')" 2>/dev/null; then
    echo "✅ FastAPI application ready"
else
    echo "❌ Application import failed"
    exit 1
fi

# Check scripts
echo
echo "📜 Checking scripts..."
if [ -x "scripts/pull_models.sh" ]; then
    echo "✅ Model pulling script executable"
else
    echo "❌ Model pulling script not executable"
    echo "   Run: chmod +x scripts/pull_models.sh"
fi

if [ -x "scripts/docker-entrypoint.sh" ]; then
    echo "✅ Docker entrypoint script executable"
else
    echo "❌ Docker entrypoint script not executable"
    echo "   Run: chmod +x scripts/docker-entrypoint.sh"
fi

if [ -x "pull-models.sh" ]; then
    echo "✅ Convenience script executable"
else
    echo "❌ Convenience script not executable"
    echo "   Run: chmod +x pull-models.sh"
fi

# Check configuration files
echo
echo "⚙️  Checking configuration..."
if [ -f "models.yaml" ]; then
    echo "✅ Models configuration found"
    model_count=$(grep -c "model_name:" models.yaml)
    echo "   Found $model_count configured models"
else
    echo "❌ models.yaml not found"
    exit 1
fi

if [ -f "docker-compose.yml" ]; then
    echo "✅ Docker Compose configuration found"
else
    echo "❌ docker-compose.yml not found"
    exit 1
fi

if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile found"
else
    echo "❌ Dockerfile not found"
    exit 1
fi

# Check Docker (optional)
echo
echo "🐳 Checking Docker (optional)..."
if command -v docker &> /dev/null; then
    echo "✅ Docker found: $(docker --version | head -1)"
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose found: $(docker-compose --version)"
    else
        echo "⚠️  Docker Compose not found (try 'docker compose' command)"
    fi
else
    echo "⚠️  Docker not found (optional for local development)"
fi

echo
echo "🎉 Setup Verification Complete!"
echo
echo "📚 Next steps:"
echo "  • Local development: make dev"
echo "  • Pull models: make pull-models"
echo "  • Docker deployment: docker-compose up"
echo "  • Run tests: make test"
echo "  • Code quality: make lint"
echo
echo "📖 See PROJECT_STATUS.md for detailed information"