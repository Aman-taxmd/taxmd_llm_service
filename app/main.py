from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers.chat import router as chat_router
from app.api.routers.health import router as health_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.logging_middleware import RequestLoggingMiddleware, SecurityAuditMiddleware
from app.services.mistral_client import get_client


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    client = await get_client()
    _ = await client.health()
    yield
    await client.aclose()


app = FastAPI(title="Bedrock LLM API", version="0.1.0", lifespan=lifespan)

app.add_middleware(SecurityAuditMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_origin_regex=r"https://.*\.taxmd\.com$",
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(chat_router, prefix="/v1", tags=["chat"])


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "bedrock-llm-api"})
