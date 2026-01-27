"""LLM client facade. Returns the Bedrock provider from the registry."""

from __future__ import annotations

from app.services.provider_registry import get_registry


async def get_client():
    """Return the Bedrock LLM provider (singleton)."""
    return get_registry()
