# Automatic Model Management

This project includes automatic model management that reads the `models.yaml` configuration and ensures all required models are available before starting the API.

## How It Works

When you run `docker-compose up`, the system will:

1. **Check models.yaml**: Read the model configuration file
2. **Query Ollama**: Check which models are already available
3. **Pull missing models**: Automatically download any missing models
4. **Start API**: Only start the API server after all models are ready

## Models Configuration

Edit `models.yaml` to configure which models should be available:

```yaml
models:
  default:
    provider: ollama
    model_name: phi4
  mistral:
    provider: ollama
    model_name: mistral
  deepseek:
    provider: ollama
    model_name: deepseek-r1:7b
```

## Manual Model Management

If you want to pre-pull models before running docker-compose:

```bash
# Pull all required models manually
./pull-models.sh

# Or use the direct script
./scripts/pull_models.sh
```

## Features

- ✅ **Automatic detection**: Only pulls missing models
- ✅ **Progress tracking**: Shows download progress for large models
- ✅ **Error handling**: Graceful handling of network issues
- ✅ **Health checks**: Waits for Ollama service to be ready
- ✅ **Docker integration**: Seamlessly integrated with docker-compose
- ✅ **Development friendly**: Works in both Docker and local development

## Environment Variables

- `OLLAMA_BASE_URL`: Ollama service URL (default: http://localhost:11434 for local, http://ollama:11434 for Docker)
- `MODELS_CONFIG`: Path to models configuration file (default: models.yaml)

## Troubleshooting

If models fail to pull:
1. Check Ollama service is running: `curl http://localhost:11434/api/tags`
2. Verify network connectivity
3. Check model names are correct in models.yaml
4. Review logs for specific error messages

The system will retry and provide clear error messages if something goes wrong.