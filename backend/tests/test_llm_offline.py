from app.llm.offline_llm import OfflineLLM


def test_offline_llm_greets_on_greeting() -> None:
    llm = OfflineLLM()
    text = "".join(llm.stream_chat(history=[], user_message="Hello!", context_chunks=[]))
    assert "offline" in text.lower()


def test_offline_llm_answers_question_without_context() -> None:
    llm = OfflineLLM()
    text = "".join(
        llm.stream_chat(history=[], user_message="What is the meaning of life?", context_chunks=[])
    )
    assert "question" in text.lower()


def test_offline_llm_produces_code_block_on_request() -> None:
    llm = OfflineLLM()
    text = "".join(
        llm.stream_chat(history=[], user_message="Show me a code example", context_chunks=[])
    )
    assert "```python" in text


def test_offline_llm_grounds_answer_in_context_chunks() -> None:
    llm = OfflineLLM()
    context = ["Refunds are processed within five business days of the request."]
    text = "".join(
        llm.stream_chat(
            history=[], user_message="How long do refunds take?", context_chunks=context
        )
    )
    assert "five business days" in text
    assert "document" in text.lower()


def test_offline_llm_is_deterministic() -> None:
    llm = OfflineLLM()
    message = "Tell me something"
    first = "".join(llm.stream_chat(history=[], user_message=message, context_chunks=[]))
    second = "".join(llm.stream_chat(history=[], user_message=message, context_chunks=[]))
    assert first == second


def test_offline_llm_streams_in_more_than_one_piece_for_long_text() -> None:
    llm = OfflineLLM()
    pieces = list(
        llm.stream_chat(
            history=[],
            user_message="hi",
            context_chunks=["a fairly long piece of context text to stream back in chunks"],
        )
    )
    assert len(pieces) > 1
    assert "".join(pieces)  # non-empty overall
