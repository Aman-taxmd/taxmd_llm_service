"""
AWS Bedrock LLM backend. Model families: claude, llama, titan, ministral.
"""

from app.bedrock.base import BedrockProvider
from app.bedrock.claude import DEFAULT_MODEL_ID as _CLAUDE_DEFAULT, MODEL_IDS as _CLAUDE_IDS
from app.bedrock.llama import DEFAULT_MODEL_ID as _LLAMA_DEFAULT, MODEL_IDS as _LLAMA_IDS
from app.bedrock.ministral import DEFAULT_MODEL_ID as _MINISTRAL_DEFAULT, MODEL_IDS as _MINISTRAL_IDS
from app.bedrock.titan import DEFAULT_MODEL_ID as _TITAN_DEFAULT, MODEL_IDS as _TITAN_IDS

__all__ = ["BedrockProvider", "get_model_id_for_family"]

FAMILIES = {
    "claude": (_CLAUDE_DEFAULT, _CLAUDE_IDS),
    "llama": (_LLAMA_DEFAULT, _LLAMA_IDS),
    "titan": (_TITAN_DEFAULT, _TITAN_IDS),
    "ministral": (_MINISTRAL_DEFAULT, _MINISTRAL_IDS),
}


def get_model_id_for_family(family: str, model: str | None = None) -> str:
    """Resolve LLM_FAMILY + optional LLM_MODEL to a Bedrock model ID."""
    key = (family or "").strip().lower() or "claude"
    default, ids = FAMILIES.get(key, (_CLAUDE_DEFAULT, _CLAUDE_IDS))
    m = (model or "").strip()
    if not m:
        return default
    if m in ids:
        return m
    return m  # assume it's already a full model ID
