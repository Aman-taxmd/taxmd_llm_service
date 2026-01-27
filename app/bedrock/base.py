"""
Base Bedrock provider using boto3 Converse / ConverseStream.
Streaming yields unified chunks: {"content", "done", "prompt_tokens", "completion_tokens"}.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _get_bedrock_client():  # noqa: ANN202
    import boto3
    from botocore.config import Config

    s = get_settings()
    kwargs = {"region_name": s.aws_region, "config": Config(read_timeout=s.bedrock_timeout)}
    if s.aws_access_key_id and s.aws_secret_access_key:
        kwargs["aws_access_key_id"] = s.aws_access_key_id
        kwargs["aws_secret_access_key"] = s.aws_secret_access_key
    return boto3.client("bedrock-runtime", **kwargs)


def _messages_to_bedrock(
    messages: list[dict[str, str]], system: str | None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Convert chat messages to Bedrock format. Returns (system_blocks, message_list)."""
    system_blocks: list[dict[str, Any]] = [{"text": system}] if system else []

    bedrock_messages: list[dict[str, Any]] = []
    for m in messages:
        role = m.get("role", "user")
        if role == "system":
            if not system_blocks:
                system_blocks = [{"text": m.get("content", "")}]
            continue
        content = m.get("content", "")
        bedrock_role = "user" if role == "user" else "assistant"
        bedrock_messages.append({"role": bedrock_role, "content": [{"text": content}]})
    return system_blocks, bedrock_messages


class BedrockProvider:
    """LLM provider for AWS Bedrock via Converse / ConverseStream."""

    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

    async def aclose(self) -> None:
        pass

    async def health(self) -> bool:
        try:
            client = _get_bedrock_client()
            await asyncio.to_thread(
                client.converse,
                modelId=self.model_id,
                messages=[{"role": "user", "content": [{"text": "Hi"}]}],
                inferenceConfig={"maxTokens": 2},
            )
            return True
        except Exception as exc:
            logger.warning("Bedrock health check failed", extra={"exc": repr(exc)})
            return False

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any] | AsyncGenerator[dict[str, Any], None]:
        settings = get_settings()
        model_id = model or self.model_id
        inference_max = max_tokens or settings.llm_max_tokens or 512
        inference_temp = (
            temperature
            if temperature is not None
            else (settings.llm_temperature if settings.llm_temperature is not None else 0.3)
        )

        system_blocks, bedrock_messages = _messages_to_bedrock(messages, system)
        inference_config: dict[str, Any] = {
            "maxTokens": inference_max,
            "temperature": inference_temp,
        }

        if stream:
            return self._stream(model_id, system_blocks, bedrock_messages, inference_config)
        return await self._complete(model_id, system_blocks, bedrock_messages, inference_config)

    async def _complete(
        self,
        model_id: str,
        system_blocks: list[dict[str, Any]],
        bedrock_messages: list[dict[str, Any]],
        inference_config: dict[str, Any],
    ) -> dict[str, Any]:
        client = _get_bedrock_client()
        kwargs: dict[str, Any] = {
            "modelId": model_id,
            "messages": bedrock_messages,
            "inferenceConfig": inference_config,
        }
        if system_blocks:
            kwargs["system"] = system_blocks
        resp = await asyncio.to_thread(client.converse, **kwargs)
        out = resp.get("output") or {}
        msg = out.get("message") or {}
        contents = msg.get("content") or []
        text = "".join(c.get("text", "") for c in contents if "text" in c)
        usage = out.get("usage") or {}
        return {
            "message": {"role": "assistant", "content": text},
            "eval_count": usage.get("outputTokens", 0),
            "prompt_eval_count": usage.get("inputTokens", 0),
            "done": True,
        }

    def _stream(
        self,
        model_id: str,
        system_blocks: list[dict[str, Any]],
        bedrock_messages: list[dict[str, Any]],
        inference_config: dict[str, Any],
    ) -> AsyncGenerator[dict[str, Any], None]:
        async def gen() -> AsyncGenerator[dict[str, Any], None]:
            client = _get_bedrock_client()
            kwargs: dict[str, Any] = {
                "modelId": model_id,
                "messages": bedrock_messages,
                "inferenceConfig": inference_config,
            }
            if system_blocks:
                kwargs["system"] = system_blocks
            resp = await asyncio.to_thread(client.converse_stream, **kwargs)
            stream = resp.get("stream")
            if not stream:
                yield {"content": "", "done": True, "prompt_tokens": None, "completion_tokens": None}
                return
            loop = asyncio.get_event_loop()
            _stop = object()

            def get_next() -> Any:
                try:
                    return next(stream)
                except StopIteration:
                    return _stop

            while True:
                event = await loop.run_in_executor(None, get_next)
                if event is _stop:
                    break
                if "contentBlockDelta" in event:
                    delta = (event["contentBlockDelta"] or {}).get("delta") or {}
                    text = delta.get("text", "") or ""
                    if text:
                        yield {"content": text, "done": False, "prompt_tokens": None, "completion_tokens": None}
                if "messageStop" in event:
                    meta = (event["messageStop"] or {}).get("metadata") or {}
                    usage = meta.get("usage") or {}
                    yield {
                        "content": "",
                        "done": True,
                        "prompt_tokens": usage.get("inputTokens"),
                        "completion_tokens": usage.get("outputTokens"),
                    }

        return gen()
