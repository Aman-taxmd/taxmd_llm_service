## AWS production deployment guide

This guide covers deploying the API service and an Ollama runtime (hosting Mistral) to AWS using ECS (Fargate), ECR, and an Application Load Balancer. Alternatives like EC2 or EKS are also viable; ECS Fargate provides a good balance for managed ops.

### Architecture
- Public ALB -> ECS Service (API) on Fargate
- Private ECS Service (Ollama) on Fargate in the same VPC/Subnets, fronted by an internal NLB or accessed via service discovery
- ECR for container images
- CloudWatch Logs for observability
- Secrets via SSM Parameter Store or Secrets Manager

### Prerequisites
- AWS account and IAM permissions for ECS/ECR/VPC/ALB/ACM/Route53
- Docker installed locally
- AWS CLI configured

### Build and push the API image
```bash
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mistral-api"

aws ecr create-repository --repository-name mistral-api || true
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build -t mistral-api:latest .
docker tag mistral-api:latest "$ECR_URI:latest"
docker push "$ECR_URI:latest"
```

### Ollama on ECS
You can run Ollama in its own ECS service with a persistent volume (EFS) for models. Example task definition snippet:

```json
{
  "family": "ollama",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "4096",
  "memory": "8192",
  "containerDefinitions": [
    {
      "name": "ollama",
      "image": "ollama/ollama:latest",
      "essential": true,
      "portMappings": [{"containerPort": 11434, "hostPort": 11434}],
      "mountPoints": [
        {
          "sourceVolume": "models",
          "containerPath": "/root/.ollama",
          "readOnly": false
        }
      ],
      "environment": [{"name": "OLLAMA_KEEP_ALIVE", "value": "5m"}],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ollama",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -sf http://localhost:11434/api/tags || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ],
  "volumes": [
    {
      "name": "models",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxxxxx",
        "transitEncryption": "ENABLED"
      }
    }
  ]
}
```

If using GPU instances (e.g., g5), add GPU resources to the task definition:

```json
"inferenceAccelerators": [],
"containerDefinitions": [{
  "resourceRequirements": [{"type": "GPU", "value": "1"}],
  "environment": [
    {"name": "OLLAMA_NUM_GPU", "value": "1"},
    {"name": "NVIDIA_VISIBLE_DEVICES", "value": "all"},
    {"name": "NVIDIA_DRIVER_CAPABILITIES", "value": "compute,utility"}
  ]
}]
```

After the service is up, exec into the container once to pull the model:
```bash
aws ecs execute-command --cluster <cluster> --task <task-id> --container ollama --command "ollama pull mistral" --interactive
```

### API service task definition
Set `OLLAMA_BASE_URL` to the Ollama service internal endpoint (Service Discovery or NLB private DNS). Example definition:

```json
{
  "family": "mistral-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<ECR_URI>:latest",
      "essential": true,
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "LOG_LEVEL", "value": "info"},
        {"name": "DEFAULT_MODEL", "value": "mistral"},
        {"name": "OLLAMA_BASE_URL", "value": "http://ollama.internal:11434"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mistral-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -sf http://localhost:8000/health/live || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

Expose the API via an ALB (HTTP 80/HTTPS 443). For HTTPS, create an ACM certificate and attach to the ALB listener; add a `Host`-based rule to forward to the ECS service target group.

### Dynamic models in production
- Bake `models.yaml` into the API image or mount via ECS task volume.
- Add any new models (e.g., DeepSeek) by updating `models.yaml` and pulling them once in the Ollama service:
  ```bash
  aws ecs execute-command --cluster <cluster> --task <task-id> --container ollama --command "ollama pull deepseek-coder:6.7b" --interactive
  ```

### Security & production hardening
- Place Ollama service in private subnets; do not expose port 11434 publicly
- Restrict API ingress via ALB security groups and WAF where applicable
- Set resource limits and autoscaling policies on ECS services
- Ship logs to CloudWatch and set alarms (5xx, latency, CPU/memory)
- Prefer SSM for secrets (if any)
- Add health checks and readiness probes (already included)

### CI/CD
- Use GitHub Actions to build/test/lint, push to ECR, and deploy via ECS
- Cache Docker layers for faster builds

### Observability
- Enable structured JSON logs (already configured)
- Add distributed tracing if needed (OpenTelemetry)

### Alternatives
- EC2: run both containers on one instance, manage via systemd + Nginx
- EKS: deploy as two Deployments with a ClusterIP for Ollama and a LoadBalancer for API

