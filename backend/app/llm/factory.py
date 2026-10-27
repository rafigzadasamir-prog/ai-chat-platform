"""Resolve which LLM backend the app should use."""

from __future__ import annotations

from app.config import get_settings
from app.llm.base import LLMBackend
from app.llm.offline_llm import OfflineLLM

_llm_instance: LLMBackend | None = None


def get_llm_backend() -> LLMBackend:
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    settings = get_settings()
    if settings.anthropic_api_key:
        import anthropic

        from app.llm.anthropic_llm import AnthropicLLM

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        _llm_instance = AnthropicLLM(client=client, model=settings.anthropic_model)
    else:
        _llm_instance = OfflineLLM()
    return _llm_instance


def set_llm_backend(backend: LLMBackend) -> None:
    """Testing hook: inject a specific backend (e.g. one wrapping a fake client)."""
    global _llm_instance
    _llm_instance = backend


def reset_llm_backend_cache() -> None:
    global _llm_instance
    _llm_instance = None
