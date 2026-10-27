"""Common interface for AI chat backends.

Every backend turns a conversation history plus optional retrieved RAG
context into a streamed, chunked text response. Routes depend only on this
interface, never on a concrete provider, so swapping/mocking a backend is
trivial (see app/llm/factory.py and the test suite's FakeAnthropicClient).
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TypedDict


class ChatMessage(TypedDict):
    role: str  # "user" | "assistant"
    content: str


class LLMBackend(ABC):
    @abstractmethod
    def stream_chat(
        self,
        history: list[ChatMessage],
        user_message: str,
        context_chunks: list[str],
    ) -> Iterator[str]:
        """Yield the AI response incrementally, piece by piece."""
        raise NotImplementedError
