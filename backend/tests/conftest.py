"""Test configuration.

Forces a fully offline, deterministic, isolated environment *before* any
``app`` module is imported: an isolated SQLite file, the dependency-free
hashing embedder (no sentence-transformers / network), and no Anthropic API
key (so the OfflineLLM backend is used everywhere the HTTP layer is
exercised). The AnthropicLLM class itself is still tested, but only via an
injected fake client -- see test_llm_anthropic.py.
"""

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

_TEST_DB_PATH = Path(tempfile.gettempdir()) / "ai_chat_platform_test.db"
if _TEST_DB_PATH.exists():
    _TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH.as_posix()}"
os.environ["SECRET_KEY"] = "test-only-secret-key-that-is-long-enough-for-hs256-signing"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["EMBEDDINGS_BACKEND"] = "hashing"
os.environ["RATE_LIMIT_MESSAGES_PER_MINUTE"] = "1000"
os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:5173"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.llm.factory import reset_llm_backend_cache  # noqa: E402
from app.main import app, limiter  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_database() -> Iterator[None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    limiter.reset()
    reset_llm_backend_cache()
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db_session() -> Iterator:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def register_and_login(
    client: TestClient, email: str = "alice@example.com", password: str = "supersecret1"
) -> str:
    """Register + log in a user through the real HTTP endpoints and return a bearer token."""
    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    token = register_and_login(client)
    return {"Authorization": f"Bearer {token}"}
