from fastapi.testclient import TestClient


def test_usage_starts_at_zero(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/usage", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"message_count": 0, "estimated_tokens": 0}


def test_usage_increments_after_messages(client: TestClient, auth_headers: dict[str, str]) -> None:
    conv = client.post("/conversations", json={}, headers=auth_headers).json()

    client.post(
        f"/conversations/{conv['id']}/messages",
        json={"content": "This is my first message to the assistant."},
        headers=auth_headers,
    )
    usage_after_one = client.get("/usage", headers=auth_headers).json()
    assert usage_after_one["message_count"] == 1
    assert usage_after_one["estimated_tokens"] > 0

    client.post(
        f"/conversations/{conv['id']}/messages",
        json={"content": "And a second one, please."},
        headers=auth_headers,
    )
    usage_after_two = client.get("/usage", headers=auth_headers).json()
    assert usage_after_two["message_count"] == 2
    assert usage_after_two["estimated_tokens"] > usage_after_one["estimated_tokens"]


def test_usage_requires_auth(client: TestClient) -> None:
    assert client.get("/usage").status_code == 401


def test_usage_is_per_user(client: TestClient) -> None:
    from tests.conftest import register_and_login

    token_a = register_and_login(client, email="usage-a@example.com")
    token_b = register_and_login(client, email="usage-b@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    conv = client.post("/conversations", json={}, headers=headers_a).json()
    client.post(
        f"/conversations/{conv['id']}/messages", json={"content": "hello"}, headers=headers_a
    )

    assert client.get("/usage", headers=headers_a).json()["message_count"] == 1
    assert client.get("/usage", headers=headers_b).json()["message_count"] == 0
