"""Bedrock-only registry: resolves LLM_FAMILY + LLM_MODEL to a BedrockProvider."""

from __future__ import annotations

from app.bedrock import BedrockProvider, get_model_id_for_family
from app.core.config import get_settings


def get_bedrock_provider() -> BedrockProvider:
    settings = get_settings()
    model_id = get_model_id_for_family(settings.llm_family, settings.llm_model or None)
    return BedrockProvider(model_id=model_id)


_provider_singleton: BedrockProvider | None = None


def get_registry() -> BedrockProvider:
    global _provider_singleton
    if _provider_singleton is None:
        _provider_singleton = get_bedrock_provider()
    return _provider_singleton
