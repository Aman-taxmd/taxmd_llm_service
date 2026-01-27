## Architecture overview

- `FastAPI` service (`/v1/chat`) acts as a thin adapter over Ollama.
- `Ollama` hosts local Mistral models, providing `/api/chat` and `/api/generate`.
- Configuration is injected via environment variables and validated via Pydantic.
- Logging is structured JSON to ease ingestion by CloudWatch/ELK.
- Tests validate basic routing and validation.

### Request flow
1. Client calls `POST /v1/chat` with `messages` and optional `system`, `temperature`, `max_tokens`.
2. Service passes the request to Ollama's `/api/chat` with streaming toggled per request.
3. Response is proxied back (or streamed as NDJSON when `stream=true`).

### Extensibility
- Add new endpoints under `app/api/routers/`.
- Implement additional providers by creating new clients in `app/services/` and switching via config.
