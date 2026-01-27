# Development Environment Architecture

This document describes the system architecture for the development environment of the Tax Assistant AI Review system.

## Overview

The development environment consists of:
- **Frontend**: User interface (React/Vue/etc.)
- **AI Backend**: Django application handling business logic and API gateway
- **AI Review Service**: FastAPI application for AI processing
- **Ollama**: Local LLM inference server (shared with staging)

## Architecture Diagram

```mermaid
graph TB
    subgraph "Development Environment"
        subgraph "Client Layer"
            FE[Frontend<br/>React/Vue App<br/>Port: 3000]
        end
        
        subgraph "API Gateway Layer"
            BE[AI Backend<br/>Django App<br/>Port: 8000]
        end
        
        subgraph "AI Processing Layer"
            AI[AI Review Service<br/>FastAPI App<br/>Port: 8002]
        end
        
        subgraph "LLM Inference Layer"
            OL[Ollama Server<br/>Port: 11434<br/>Shared with Staging]
        end
        
        subgraph "Storage Layer"
            DB[(PostgreSQL<br/>Port: 5432)]
            CACHE[(Redis<br/>Port: 6379)]
        end
    end
    
    %% Client to Backend
    FE -->|HTTP/REST API<br/>Tax queries, Document upload| BE
    
    %% Backend to AI Service
    BE -->|HTTP/REST API<br/>Document analysis requests| AI
    
    %% AI Service to Ollama
    AI -->|HTTP API<br/>LLM inference requests| OL
    
    %% Backend to Storage
    BE --> DB
    BE --> CACHE
    
    %% Response flow
    OL -->|AI responses| AI
    AI -->|Processed results| BE
    BE -->|Tax advice, Analysis| FE
    
    %% Styling
    classDef frontend fill:#e1f5fe
    classDef backend fill:#f3e5f5
    classDef ai fill:#e8f5e8
    classDef llm fill:#fff3e0
    classDef storage fill:#fce4ec
    
    class FE frontend
    class BE backend
    class AI ai
    class OL llm
    class DB,CACHE storage
```

## Component Details

### Frontend
- **Technology**: React/Vue.js application
- **Port**: 3000 (development server)
- **Responsibilities**:
  - User interface for tax queries
  - Document upload interface
  - Display AI-generated tax advice
  - Authentication UI

### AI Backend (Django)
- **Technology**: Django REST Framework
- **Port**: 8000
- **Responsibilities**:
  - API gateway and request routing
  - User authentication and authorization
  - Business logic validation
  - Data persistence and caching
  - Rate limiting and security

### AI Review Service (FastAPI)
- **Technology**: FastAPI with Python
- **Port**: 8002
- **Responsibilities**:
  - AI processing coordination
  - Document parsing and analysis
  - LLM prompt engineering
  - Response post-processing
  - Model management

### Ollama Server
- **Technology**: Ollama LLM inference engine
- **Port**: 11434
- **Models**: Mistral, Llama, etc.
- **Responsibilities**:
  - LLM inference
  - Model loading and management
  - GPU acceleration (if available)
  - **Note**: Shared between development and staging environments

## Request Flow

1. **User Interaction**: User submits tax query or document via Frontend
2. **API Gateway**: Django backend receives request, validates, and authenticates
3. **Business Logic**: Django processes business rules and prepares AI request
4. **AI Processing**: FastAPI service receives structured request
5. **LLM Inference**: Ollama processes the AI request using appropriate model
6. **Response Processing**: FastAPI post-processes the LLM response
7. **Result Delivery**: Response flows back through Django to Frontend

## Development Features

- **Hot Reload**: All services support hot reload for development
- **Debug Mode**: Detailed logging and error messages
- **Shared Resources**: Ollama instance shared with staging for cost efficiency
- **Local Development**: All services can run locally with Docker Compose

## Environment Variables

```bash
# Django Backend
DEBUG=true
DATABASE_URL=postgresql://user:pass@localhost:5432/taxassistant_dev
REDIS_URL=redis://localhost:6379
AI_REVIEW_SERVICE_URL=http://localhost:8002

# FastAPI AI Service
ENVIRONMENT=development
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=mistral
LOG_LEVEL=debug

# Ollama
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_MODELS=/models
```

## Security Considerations

- **Development Only**: Relaxed security settings for development ease
- **CORS**: Permissive CORS settings for local development
- **Authentication**: Simplified auth for testing
- **Logging**: Verbose logging for debugging

## Monitoring and Debugging

- **Health Checks**: Available on `/health` endpoints
- **Metrics**: Basic metrics collection
- **Logs**: Structured logging with request tracing
- **Debug Tools**: Django Debug Toolbar, FastAPI auto-docs