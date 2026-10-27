from fastapi.testclient import TestClient

from tests.conftest import register_and_login


def test_register_creates_user(client: TestClient) -> None:
    response = client.post(
        "/auth/register", json={"email": "new@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "id" in body
    assert "hashed_password" not in body  # never leak the hash


def test_register_duplicate_email_rejected(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})
    response = client.post(
        "/auth/register", json={"email": "dup@example.com", "password": "password123"}
    )
    assert response.status_code == 400


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post("/auth/register", json={"email": "short@example.com", "password": "123"})
    assert response.status_code == 422


def test_login_success_returns_token(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "login@example.com", "password": "password123"})
    response = client.post(
        "/auth/login", json={"email": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 10


def test_login_wrong_password_rejected(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "wrongpw@example.com", "password": "password123"})
    response = client.post(
        "/auth/login", json={"email": "wrongpw@example.com", "password": "nope-not-it"}
    )
    assert response.status_code == 401


def test_login_unknown_email_rejected(client: TestClient) -> None:
    response = client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": "password123"}
    )
    assert response.status_code == 401


def test_protected_route_requires_token(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_protected_route_rejects_invalid_token(client: TestClient) -> None:
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_protected_route_accepts_valid_token(client: TestClient) -> None:
    token = register_and_login(client, email="valid@example.com")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "valid@example.com"
