from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.bedrock import get_model_id_for_family
from app.core.config import get_settings
from app.core.logging import get_request_id
from app.services.mistral_client import get_client

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    model: str | None = None  # Bedrock model ID or leave unset to use LLM_FAMILY/LLM_MODEL
    system: str | None = None
    messages: list[ChatMessage]
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0, le=8000)  # Will be set from config in __init__
    stream: bool = False
    options: dict[str, Any] | None = None
    
    def __init__(self, **data):
        settings = get_settings()
        if "temperature" not in data or data["temperature"] is None:
            data["temperature"] = (
                settings.llm_temperature if settings.llm_temperature is not None else 0.3
            )
        if "model" not in data or data["model"] is None:
            data["model"] = None
        if "max_tokens" not in data or data["max_tokens"] is None:
            data["max_tokens"] = (
                settings.llm_max_tokens
                if settings.llm_max_tokens is not None
                else settings.default_max_tokens
            )
        super().__init__(**data)


@router.post("/chat", response_model=None)
async def chat_endpoint(req: ChatRequest) -> JSONResponse | StreamingResponse:
    start_time = time.time()
    request_id = get_request_id()
    
    # Log chat request details (sanitized for SOC 2 compliance)
    logger.info(
        "chat.request.received",
        extra={
            "request_id": request_id,
            "model": req.model,
            "message_count": len(req.messages),
            "stream_requested": req.stream,
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
        }
    )
    
    settings = get_settings()
    client = await get_client()
    messages = [m.model_dump() for m in req.messages]
    # Resolve model: use req.model if provided, else use default from LLM_FAMILY
    resolved_model_id = get_model_id_for_family(settings.llm_family, req.model)
    # For response display: use req.model if provided, else show resolved model
    display_model = req.model or resolved_model_id

    if req.stream:
        async def event_gen() -> AsyncGenerator[bytes, None]:
            chunk_id = f"chatcmpl-{int(time.time())}"
            created_timestamp = int(time.time())
            try:
                stream_result = await client.chat(
                    messages=messages,
                    model=resolved_model_id,
                    system=req.system,
                    temperature=req.temperature,
                    max_tokens=req.max_tokens,
                    stream=True,
                    options=req.options,
                )
                
                # Ensure we have a generator, not a dict
                if isinstance(stream_result, dict):
                    raise HTTPException(status_code=500, detail="Expected streaming response but got complete result")
                
                # Send initial chunk immediately
                initial_chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": created_timestamp,
                    "model": display_model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant", "content": ""},
                            "finish_reason": None
                        }
                    ]
                }
                yield f"data: {json.dumps(initial_chunk)}\n\n".encode()
                
                # Stream content chunks (unified format from Bedrock)
                async for raw_chunk in stream_result:
                    try:
                        content = raw_chunk.get("content", "")
                        done = raw_chunk.get("done", False)
                        prompt_tok = raw_chunk.get("prompt_tokens")
                        comp_tok = raw_chunk.get("completion_tokens")

                        # Create ChatGPT-style streaming chunk
                        stream_chunk = {
                            "id": chunk_id,
                            "object": "chat.completion.chunk",
                            "created": created_timestamp,
                            "model": display_model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": content} if content else {},
                                    "finish_reason": None
                                }
                            ]
                        }
                        yield f"data: {json.dumps(stream_chunk)}\n\n".encode()

                        if done:
                            final_chunk = {
                                "id": chunk_id,
                                "object": "chat.completion.chunk",
                                "created": created_timestamp,
                                "model": display_model,
                                "choices": [
                                    {"index": 0, "delta": {}, "finish_reason": "stop"}
                                ],
                                "usage": {
                                    "prompt_tokens": prompt_tok or 0,
                                    "completion_tokens": comp_tok or 0,
                                    "total_tokens": (prompt_tok or 0) + (comp_tok or 0),
                                },
                                "timing": {"api_duration_seconds": round(time.time() - start_time, 3)},
                            }
                            yield f"data: {json.dumps(final_chunk)}\n\n".encode()
                            
                    except Exception as chunk_error:
                        logger.warning(f"Error processing streaming chunk: {chunk_error}")
                        continue
                
                # Send [DONE] marker
                yield b"data: [DONE]\n\n"
                
            except Exception as exc:
                logger.error(f"Streaming chat endpoint error: {exc}", exc_info=True)
                error_chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": created_timestamp,
                    "model": display_model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {},
                            "finish_reason": "error"
                        }
                    ],
                    "error": {"message": f"Upstream error: {exc!s}"}
                }
                yield f"data: {json.dumps(error_chunk)}\n\n".encode()
                yield b"data: [DONE]\n\n"

        return StreamingResponse(event_gen(), media_type="text/plain", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})

    # Handle non-streaming case
    try:
        result = await client.chat(
            messages=messages,
            model=resolved_model_id,
            system=req.system,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            stream=False,
            options=req.options,
        )
    except Exception as exc:
        logger.error(f"Chat endpoint error: {exc}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Upstream error: {exc!s}") from exc

    assert isinstance(result, dict)
    
    # Add timing information (Bedrock doesn't return internal timing like Ollama)
    api_duration = time.time() - start_time
    result["timing"] = {
        "api_duration": f"{api_duration:.2f}s",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "timestamp_iso": datetime.now().isoformat(),
    }
    
    # Log successful completion
    logger.info(
        "chat.request.completed",
        extra={
            "request_id": request_id,
            "duration_seconds": api_duration,
            "tokens_generated": result.get("eval_count", 0),
            "tokens_prompt": result.get("prompt_eval_count", 0),
        }
    )
    
    return JSONResponse(result)
