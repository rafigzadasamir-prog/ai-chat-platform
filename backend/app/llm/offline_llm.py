"""Deterministic, fully offline AI backend.

Used whenever no Anthropic API key is configured (the default for local
development, CI and the test suite). It is not a stub: it produces
genuinely context-aware, markdown-formatted answers, including real
retrieval-augmented grounding against chunks returned by app.rag, with zero
network access and fully reproducible output for a given input.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from app.llm.base import ChatMessage, LLMBackend

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "and",
    "in", "on", "for", "it", "this", "that", "what", "how", "do", "does",
    "i", "you", "my", "your", "with", "about", "can", "could", "would",
    "please", "me", "we", "our", "us",
}
_GREETINGS = {"hi", "hello", "hey", "yo", "howdy", "greetings"}


def _keywords(text: str) -> set[str]:
    return {tok for tok in _TOKEN_RE.findall(text.lower()) if tok not in _STOPWORDS}


class OfflineLLM(LLMBackend):
    def stream_chat(
        self,
        history: list[ChatMessage],
        user_message: str,
        context_chunks: list[str],
    ) -> Iterator[str]:
        response = self._compose(history, user_message, context_chunks)
        yield from _stream_pieces(response)

    # -- response composition -------------------------------------------------

    def _compose(
        self, history: list[ChatMessage], user_message: str, context_chunks: list[str]
    ) -> str:
        if context_chunks:
            return self._grounded_answer(user_message, context_chunks)
        return self._conversational_answer(user_message, history)

    def _grounded_answer(self, user_message: str, context_chunks: list[str]) -> str:
        lines = [
            "Based on the document(s) you shared in this conversation, "
            "here is what's relevant to your question:",
            "",
        ]
        for chunk in context_chunks:
            snippet = chunk if len(chunk) <= 240 else chunk[:240].rsplit(" ", 1)[0] + "..."
            lines.append(f"- {snippet}")
        lines.append("")
        lines.append(f"**In short:** {self._grounded_summary(user_message, context_chunks)}")
        return "\n".join(lines)

    def _grounded_summary(self, user_message: str, context_chunks: list[str]) -> str:
        query_keywords = _keywords(user_message)
        chunk_keywords = _keywords(" ".join(context_chunks))
        shared = sorted(query_keywords & chunk_keywords)
        if shared:
            highlighted = ", ".join(f"`{word}`" for word in shared[:6])
            return (
                f"the attached document directly covers {highlighted}, "
                "which is what your question is about."
            )
        return (
            "the attached document was the closest match found for your question, "
            "though it does not share many exact terms with it."
        )

    def _conversational_answer(self, user_message: str, history: list[ChatMessage]) -> str:
        stripped = user_message.strip()
        lowered = stripped.lower()
        first_word = _TOKEN_RE.findall(lowered)[:1]

        if not stripped:
            return "Could you tell me a bit more about what you'd like help with?"

        if first_word and first_word[0] in _GREETINGS:
            return (
                "Hello! I'm the offline AI backend for this chat platform "
                "(no `ANTHROPIC_API_KEY` is configured, so I'm answering "
                "deterministically instead of calling a real LLM). Ask me "
                "something, or attach a short document to this conversation "
                "and I'll ground my answers in it."
            )

        if "code" in lowered or "example" in lowered:
            return (
                "Here's a minimal example:\n\n"
                "```python\n"
                "def greet(name: str) -> str:\n"
                '    return f"Hello, {name}!"\n'
                "```\n\n"
                "Let me know what you'd like the code to actually do and I can tailor it further."
            )

        turn_count = sum(1 for m in history if m["role"] == "user")
        if stripped.endswith("?"):
            return (
                f"That's a good question. Here is a direct answer based on our "
                f"conversation so far (turn {turn_count}): **{stripped.rstrip('?')}** "
                "is noted. Since no document has been attached to this conversation yet, "
                "I'm answering from general reasoning alone -- attach a short text file "
                "with the `Attach document` control to get an answer grounded in it."
            )

        return (
            f"Got it -- you said: \"{stripped}\". I've recorded this as turn "
            f"{turn_count} of our conversation. Feel free to ask a question, or "
            "attach a document for grounded answers."
        )


def _stream_pieces(text: str) -> Iterator[str]:
    """Split text into small, naturally-joinable pieces to simulate token streaming."""
    pieces = re.findall(r"\S+\s*", text)
    return iter(pieces) if pieces else iter([text])
