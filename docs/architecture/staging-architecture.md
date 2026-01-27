# Staging Environment Architecture

This document describes the system architecture for the staging environment of the Tax Assistant AI Review system.

## Overview

The staging environment mirrors production but with shared resources for cost optimization:
- **Frontend**: Production-like build served via CDN/Load Balancer
- **AI Backend**: Django application with production settings
- **AI Review Service**: FastAPI application with production configurations
- **Ollama**: Shared LLM inference server (shared with development)

## Architecture Diagram

```mermaid
graph TB
    subgraph "Staging Environment"
        subgraph "Load Balancer Layer"
            LB[Load Balancer<br/>NGINX/AWS ALB<br/>Port: 443/80]
        end
        
        subgraph "Frontend Layer"
            FE[Frontend<br/>Static Build<br/>Served via CDN]
        end
        
        subgraph "API Gateway Layer"
            BE1[AI Backend Instance 1<br/>Django App<br/>Port: 8000]
            BE2[AI Backend Instance 2<br/>Django App<br/>Port: 8000]
        end
        
        subgraph "AI Processing Layer"
            AI1[AI Review Service 1<br/>FastAPI App<br/>Port: 8002]
            AI2[AI Review Service 2<br/>FastAPI App<br/>Port: 8002]
        end
        
        subgraph "Shared LLM Layer"
            OL[Ollama Server<br/>Port: 11434<br/>Shared with Development<br/>⚠️ Resource Contention]
        end
        
        subgraph "Storage Layer"
            DB[(PostgreSQL<br/>Staging Database<br/>Port: 5432)]
            CACHE[(Redis Cluster<br/>Port: 6379)]
            S3[(AWS S3<br/>Staging Bucket)]
        end
        
        subgraph "Monitoring Layer"
            LOGS[Centralized Logging<br/>ELK/CloudWatch]
            METRICS[Metrics Collection<br/>Prometheus/DataDog]
        end
    end
    
    %% External Traffic
    USERS[Users/Testers] -->|HTTPS| LB
    
    %% Load Balancer routing
    LB -->|Static Content| FE
    LB -->|API Requests| BE1
    LB -->|API Requests| BE2
    
    %% Backend to AI Service (Load Balanced)
    BE1 -->|HTTP API| AI1
    BE1 -->|HTTP API| AI2
    BE2 -->|HTTP API| AI1
    BE2 -->|HTTP API| AI2
    
    %% AI Service to Ollama (Shared Resource)
    AI1 -->|HTTP API<br/>Queue Management| OL
    AI2 -->|HTTP API<br/>Queue Management| OL
    
    %% Storage connections
    BE1 --> DB
    BE2 --> DB
    BE1 --> CACHE
    BE2 --> CACHE
    BE1 --> S3
    BE2 --> S3
    
    %% Monitoring
    BE1 --> LOGS
    BE2 --> LOGS
    AI1 --> LOGS
    AI2 --> LOGS
    BE1 --> METRICS
    BE2 --> METRICS
    AI1 --> METRICS
    AI2 --> METRICS
    
    %% Response flow
    OL -->|AI responses| AI1
    OL -->|AI responses| AI2
    AI1 -->|Processed results| BE1
    AI1 -->|Processed results| BE2
    AI2 -->|Processed results| BE1
    AI2 -->|Processed results| BE2
    BE1 -->|JSON Response| LB
    BE2 -->|JSON Response| LB
    LB -->|HTTPS Response| USERS
    
    %% Styling
    classDef frontend fill:#e1f5fe
    classDef backend fill:#f3e5f5
    classDef ai fill:#e8f5e8
    classDef llm fill:#fff3e0
    classDef storage fill:#fce4ec
    classDef monitoring fill:#f0f4c3
    classDef loadbalancer fill:#e8eaf6
    classDef warning fill:#ffebee
    
    class FE frontend
    class BE1,BE2 backend
    class AI1,AI2 ai
    class OL warning
    class DB,CACHE,S3 storage
    class LOGS,METRICS monitoring
    class LB loadbalancer
```

## Component Details

### Load Balancer
- **Technology**: NGINX or AWS Application Load Balancer
- **Responsibilities**:
  - SSL termination
  - Request routing
  - Health checking
  - Rate limiting
  - Static content serving

### Frontend
- **Technology**: Production build served via CDN
- **Responsibilities**:
  - Optimized static assets
  - CDN caching
  - Production-like performance testing

### AI Backend (Django) - Multiple Instances
- **Technology**: Django with Gunicorn/uWSGI
- **Scaling**: 2+ instances behind load balancer
- **Responsibilities**:
  - Production-like API gateway
  - Authentication and authorization
  - Business logic validation
  - Request queuing and load distribution

### AI Review Service (FastAPI) - Multiple Instances
- **Technology**: FastAPI with Uvicorn
- **Scaling**: 2+ instances for redundancy
- **Responsibilities**:
  - AI processing coordination
  - Request queuing for shared Ollama
  - Timeout and retry management
  - Response caching

### Shared Ollama Server
- **Technology**: Single Ollama instance
- **⚠️ Resource Contention**: Shared between dev and staging
- **Responsibilities**:
  - LLM inference for both environments
  - Request queuing and prioritization
  - Model management
  - **Risk**: Performance degradation during concurrent usage

## Request Flow

1. **User Request**: HTTPS request hits load balancer
2. **Load Balancing**: Request routed to available Django instance
3. **Authentication**: User authentication and rate limiting
4. **Business Logic**: Django processes and validates request
5. **AI Service Selection**: Load balancer routes to available FastAPI instance
6. **Queue Management**: FastAPI queues request for shared Ollama
7. **LLM Processing**: Ollama processes request (may queue due to sharing)
8. **Response Processing**: FastAPI processes LLM response
9. **Result Delivery**: Response flows back through load balancer

## Shared Resource Management

### Ollama Sharing Strategy
```mermaid
graph LR
    subgraph "Request Queue Management"
        DEV[Development Requests] -->|Priority: Low| QUEUE[Request Queue]
        STAGE[Staging Requests] -->|Priority: High| QUEUE
        QUEUE --> OL[Ollama Server]
    end
    
    subgraph "Resource Allocation"
        OL -->|Response| DEV
        OL -->|Response| STAGE
    end
```

## Environment Variables

```bash
# Load Balancer
SSL_CERT_PATH=/etc/ssl/certs/staging.crt
SSL_KEY_PATH=/etc/ssl/private/staging.key

# Django Backend
DEBUG=false
ENVIRONMENT=staging
DATABASE_URL=postgresql://user:pass@staging-db:5432/taxassistant_staging
REDIS_URL=redis://staging-redis-cluster:6379
AI_REVIEW_SERVICE_URL=http://ai-review-service:8002
ALLOWED_HOSTS=staging.taxassistant.com

# FastAPI AI Service
ENVIRONMENT=staging
OLLAMA_BASE_URL=http://shared-ollama:11434
DEFAULT_MODEL=mistral
LOG_LEVEL=info
QUEUE_MAX_SIZE=50
REQUEST_TIMEOUT=120

# Ollama (Shared)
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_MAX_LOADED_MODELS=2
OLLAMA_NUM_PARALLEL=4
OLLAMA_KEEP_ALIVE=5m
```

## Monitoring and Alerting

### Health Checks
- **Load Balancer**: Monitor backend health
- **Services**: `/health` endpoint monitoring
- **Ollama**: Queue depth and response time monitoring

### Key Metrics
- **Response Time**: API response latencies
- **Queue Depth**: Ollama request queue size
- **Error Rates**: 4xx/5xx error percentages
- **Resource Utilization**: CPU/Memory usage
- **Concurrent Users**: Active session count

### Alerts
- **High Queue Depth**: Ollama request queue > 10
- **Response Time**: API response time > 5s
- **Error Rate**: Error rate > 5%
- **Resource Contention**: Concurrent dev/staging usage

## Testing Scenarios

### Load Testing
- **User Simulation**: Concurrent user testing
- **Resource Sharing**: Test dev/staging concurrent usage
- **Performance Degradation**: Monitor shared Ollama impact

### Integration Testing
- **End-to-End**: Complete user journey testing
- **Failover**: Service instance failure testing
- **Queue Management**: High-load queue behavior

## Limitations and Risks

### Shared Ollama Risks
- **Performance Degradation**: Dev usage impacts staging
- **Resource Competition**: Queue buildup during peak usage
- **Single Point of Failure**: Shared service outage affects both environments

### Mitigation Strategies
- **Request Prioritization**: Staging requests get higher priority
- **Queue Limits**: Max queue depth per environment
- **Monitoring**: Active queue depth and response time monitoring
- **Fallback**: Plan for dedicated staging Ollama if needed