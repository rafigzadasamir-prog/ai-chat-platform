"""Tests for AnthropicLLM using an injected fake client -- no network, no API key."""

from typing import Any

from app.llm.anthropic_llm import AnthropicLLM


class _FakeStreamContext:
    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks

    def __enter__(self) -> "_FakeStreamContext":
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False

    @property
    def text_stream(self) -> Any:
        return iter(self._chunks)


class _FakeMessages:
    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks
        self.calls: list[dict] = []

    def stream(self, **kwargs: Any) -> _FakeStreamContext:
        self.calls.append(kwargs)
        return _FakeStreamContext(self._chunks)


class FakeAnthropicClient:
    def __init__(self, chunks: list[str]) -> None:
        self.messages = _FakeMessages(chunks)


def test_anthropic_llm_yields_streamed_chunks() -> None:
    fake_client = FakeAnthropicClient(["Hello", ", ", "world", "!"])
    llm = AnthropicLLM(client=fake_client, model="claude-sonnet-5")

    chunks = list(llm.stream_chat(history=[], user_message="hi", context_chunks=[]))

    assert chunks == ["Hello", ", ", "world", "!"]


def test_anthropic_llm_sends_correct_model_and_message() -> None:
    fake_client = FakeAnthropicClient(["ok"])
    llm = AnthropicLLM(client=fake_client, model="claude-sonnet-5")

    list(llm.stream_chat(history=[], user_message="How are you?", context_chunks=[]))

    call = fake_client.messages.calls[0]
    assert call["model"] == "claude-sonnet-5"
    assert call["messages"][-1] == {"role": "user", "content": "How are you?"}


def test_anthropic_llm_includes_history_in_order() -> None:
    fake_client = FakeAnthropicClient(["ok"])
    llm = AnthropicLLM(client=fake_client, model="claude-sonnet-5")
    history = [
        {"role": "user", "content": "first message"},
        {"role": "assistant", "content": "first reply"},
    ]

    list(llm.stream_chat(history=history, user_message="second message", context_chunks=[]))

    call = fake_client.messages.calls[0]
    assert call["messages"] == [
        {"role": "user", "content": "first message"},
        {"role": "assistant", "content": "first reply"},
        {"role": "user", "content": "second message"},
    ]


def test_anthropic_llm_grounds_system_prompt_with_context_chunks() -> None:
    fake_client = FakeAnthropicClient(["ok"])
    llm = AnthropicLLM(client=fake_client, model="claude-sonnet-5")

    list(
        llm.stream_chat(
            history=[],
            user_message="What does the doc say?",
            context_chunks=["refunds take five business days"],
        )
    )

    call = fake_client.messages.calls[0]
    assert "refunds take five business days" in call["system"]


def test_anthropic_llm_system_prompt_has_no_context_section_when_no_chunks() -> None:
    fake_client = FakeAnthropicClient(["ok"])
    llm = AnthropicLLM(client=fake_client, model="claude-sonnet-5")

    list(llm.stream_chat(history=[], user_message="hi", context_chunks=[]))

    call = fake_client.messages.calls[0]
    assert "retrieved as relevant" not in call["system"]
