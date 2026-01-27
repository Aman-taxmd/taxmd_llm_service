import asyncio
import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.services.mistral_client import get_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/live")
async def live() -> JSONResponse:
    """Liveness check - service is running."""
    return JSONResponse({"status": "live", "timestamp": time.time()})


@router.get("/ready")
async def ready() -> JSONResponse:
    """
    Readiness check with configurable timeout.
    
    Uses HEALTH_CHECK_TIMEOUT_SECONDS environment variable (default: 300s/5min)
    for improved resource optimization.
    """
    settings = get_settings()
    
    try:
        # Use asyncio.wait_for to implement configurable timeout
        client = await get_client()
        
        start_time = time.time()
        ok = await asyncio.wait_for(
            client.health(), 
            timeout=settings.health_check_timeout_seconds
        )
        check_duration = round((time.time() - start_time) * 1000, 2)
        
        logger.info(
            "health_check.ready",
            extra={
                "bedrock_status": ok,
                "duration_ms": check_duration,
                "timeout_configured_seconds": settings.health_check_timeout_seconds,
            },
        )
        return JSONResponse({
            "status": "ready" if ok else "not_ready",
            "bedrock": ok,
            "check_duration_ms": check_duration,
            "timeout_seconds": settings.health_check_timeout_seconds,
            "timestamp": time.time(),
        })
        
    except asyncio.TimeoutError:
        logger.warning(
            "health_check.timeout",
            extra={
                "timeout_seconds": settings.health_check_timeout_seconds,
                "timestamp": time.time()
            }
        )
        raise HTTPException(
            status_code=503,
            detail={
                "status": "timeout",
                "message": f"Health check timed out after {settings.health_check_timeout_seconds} seconds",
                "timeout_seconds": settings.health_check_timeout_seconds
            }
        )
    except Exception as exc:
        logger.error(
            "health_check.error",
            extra={"error": str(exc)},
            exc_info=True
        )
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": "Health check failed",
                "error": str(exc)
            }
        )


@router.get("/performance")
async def performance() -> JSONResponse:
    """Bedrock model configuration."""
    settings = get_settings()
    return JSONResponse({
        "llm_family": settings.llm_family,
        "llm_model": settings.llm_model or "(default for family)",
        "llm_temperature": settings.llm_temperature,
        "llm_max_tokens": settings.llm_max_tokens,
        "aws_region": settings.aws_region,
    })
