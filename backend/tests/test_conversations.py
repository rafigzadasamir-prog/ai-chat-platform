import json

from fastapi.testclient import TestClient

from tests.conftest import register_and_login


def _parse_sse(raw_text: str) -> list[tuple[str, dict]]:
    """Parse a full (already-consumed) SSE response body into (event, data) pairs."""
    events = []
    for block in raw_text.split("\n\n"):
        if not block.strip():
            continue
        event_name = "message"
        data_line = None
        for line in block.splitlines():
            if line.startswith("event:"):
                event_name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_line = line.removeprefix("data:").strip()
        if data_line is not None:
            events.append((event_name, json.loads(data_line)))
    return events


def test_create_and_list_conversations(client: TestClient, auth_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/conversations", json={"title": "My first chat"}, headers=auth_headers
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "My first chat"

    list_response = client.get("/conversations", headers=auth_headers)
    assert list_response.status_code == 200
    conversations = list_response.json()
    assert len(conversations) == 1
    assert conversations[0]["id"] == created["id"]


def test_create_conversation_default_title(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post("/conversations", json={}, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["title"] == "New conversation"


def test_conversations_require_auth(client: TestClient) -> None:
    response = client.get("/conversations")
    assert response.status_code == 401


def test_user_cannot_access_another_users_conversation(client: TestClient) -> None:
    token_a = register_and_login(client, email="owner@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    conv = client.post("/conversations", json={}, headers=headers_a).json()

    token_b = register_and_login(client, email="intruder@example.com")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    read_response = client.get(f"/conversations/{conv['id']}/messages", headers=headers_b)
    assert read_response.status_code == 404

    message_response = client.post(
        f"/conversations/{conv['id']}/messages", json={"content": "hi"}, headers=headers_b
    )
    assert message_response.status_code == 404


def test_message_flow_streams_and_persists_offline_response(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    conv = client.post("/conversations", json={}, headers=auth_headers).json()

    response = client.post(
        f"/conversations/{conv['id']}/messages",
        json={"content": "Hello there, how are you?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(response.text)
    chunk_events = [data["chunk"] for name, data in events if name == "message"]
    done_events = [data for name, data in events if name == "done"]
    assert chunk_events, "expected at least one streamed chunk"
    assert len(done_events) == 1
    assert "message_id" in done_events[0]

    full_text = "".join(chunk_events)
    assert full_text  # the OfflineLLM always produces a non-empty answer

    history = client.get(f"/conversations/{conv['id']}/messages", headers=auth_headers).json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello there, how are you?"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == full_text


def test_rag_document_upload_grounds_subsequent_answer(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    conv = client.post("/conversations", json={}, headers=auth_headers).json()
    conv_id = conv["id"]

    document_text = (
        "The AI Chat Platform refund policy: customers can request a full "
        "refund within fourteen days of purchase by emailing billing@example.com. "
        "Refunds are processed within five business days."
    )
    files = {"file": ("refund-policy.txt", document_text, "text/plain")}
    upload_response = client.post(
        f"/conversations/{conv_id}/documents", files=files, headers=auth_headers
    )
    assert upload_response.status_code == 201
    upload_body = upload_response.json()
    assert upload_body["document_name"] == "refund-policy.txt"
    assert upload_body["chunk_count"] >= 1

    list_docs_response = client.get(f"/conversations/{conv_id}/documents", headers=auth_headers)
    assert list_docs_response.status_code == 200
    assert list_docs_response.json() == [
        {"document_name": "refund-policy.txt", "chunk_count": upload_body["chunk_count"]}
    ]

    ask_response = client.post(
        f"/conversations/{conv_id}/messages",
        json={"content": "What is the refund policy?"},
        headers=auth_headers,
    )
    assert ask_response.status_code == 200
    events = _parse_sse(ask_response.text)
    full_text = "".join(data["chunk"] for name, data in events if name == "message")

    # The offline LLM grounds its answer by quoting retrieved chunks verbatim.
    assert "refund" in full_text.lower()
    assert "billing@example.com" in full_text


def test_document_upload_rejects_empty_file(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    conv = client.post("/conversations", json={}, headers=auth_headers).json()
    files = {"file": ("empty.txt", "   ", "text/plain")}
    response = client.post(
        f"/conversations/{conv['id']}/documents", files=files, headers=auth_headers
    )
    assert response.status_code == 400


def test_message_to_missing_conversation_returns_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/conversations/999999/messages", json={"content": "hi"}, headers=auth_headers
    )
    assert response.status_code == 404
