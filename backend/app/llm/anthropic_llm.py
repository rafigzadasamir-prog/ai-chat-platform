"""Real AI backend: Anthropic's Claude via the official SDK, streamed.

Only instantiated when ``ANTHROPIC_API_KEY`` is set (see factory.py). The
Anthropic ``client`` is injected so tests can exercise this class with a
fake client and assert the exact prompt construction without any network
access or secret.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.llm.base import ChatMessage, LLMBackend

SYSTEM_PROMPT_BASE = (
    "You are the AI assistant inside a chat SaaS product called AI Chat "
    "Platform. Be concise, helpful, and format answers in markdown when it "
    "aids readability (lists, code blocks)."
)


def build_system_prompt(context_chunks: list[str]) -> str:
    if not context_chunks:
        return SYSTEM_PROMPT_BASE
    joined = "\n\n".join(f"- {chunk}" for chunk in context_chunks)
    return (
        f"{SYSTEM_PROMPT_BASE}\n\n"
        "The user has attached document(s) to this conversation. The "
        "following excerpts were retrieved as relevant to their latest "
        f"message -- ground your answer in them when applicable:\n\n{joined}"
    )


class AnthropicLLM(LLMBackend):
    def __init__(self, client: Any, model: str) -> None:
        self._client = client
        self._model = model

    def stream_chat(
        self,
        history: list[ChatMessage],
        user_message: str,
        context_chunks: list[str],
    ) -> Iterator[str]:
        system_prompt = build_system_prompt(context_chunks)
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": user_message})

        with self._client.messages.stream(
            model=self._model,
            max_tokens=2048,
            system=system_prompt,
            messages=messages,
        ) as stream:
            yield from stream.text_stream
