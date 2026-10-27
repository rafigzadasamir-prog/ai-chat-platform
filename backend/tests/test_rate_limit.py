import time

from fastapi.testclient import TestClient

from app.main import limiter
from app.rate_limit import RateLimiter, TokenBucket


def test_token_bucket_blocks_once_exhausted() -> None:
    bucket = TokenBucket(capacity=2, refill_per_second=0.0)
    assert bucket.try_consume() is True
    assert bucket.try_consume() is True
    assert bucket.try_consume() is False  # exhausted, and refill rate is 0


def test_token_bucket_refills_over_time() -> None:
    bucket = TokenBucket(capacity=1, refill_per_second=100.0)
    assert bucket.try_consume() is True
    assert bucket.try_consume() is False
    time.sleep(0.1)  # 100 tokens/sec * 0.1s = ~10 tokens refilled, well above 1 needed
    assert bucket.try_consume() is True


def test_rate_limiter_tracks_separate_keys_independently() -> None:
    rate_limiter = RateLimiter(capacity_per_minute=1)
    assert rate_limiter.allow("user-a") is True
    assert rate_limiter.allow("user-a") is False
    assert rate_limiter.allow("user-b") is True  # different key, own bucket


def test_message_endpoint_returns_429_once_exceeded(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    original_capacity = limiter.capacity_per_minute
    limiter.capacity_per_minute = 2
    limiter.reset()
    try:
        conv = client.post("/conversations", json={}, headers=auth_headers).json()
        statuses = [
            client.post(
                f"/conversations/{conv['id']}/messages",
                json={"content": "hi"},
                headers=auth_headers,
            ).status_code
            for _ in range(4)
        ]
        assert statuses[:2] == [200, 200]
        assert 429 in statuses[2:]
    finally:
        limiter.capacity_per_minute = original_capacity
        limiter.reset()


def test_other_routes_are_unaffected_by_rate_limit(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    original_capacity = limiter.capacity_per_minute
    limiter.capacity_per_minute = 1
    limiter.reset()
    try:
        conv = client.post("/conversations", json={}, headers=auth_headers).json()
        client.post(
            f"/conversations/{conv['id']}/messages", json={"content": "hi"}, headers=auth_headers
        )
        client.post(
            f"/conversations/{conv['id']}/messages", json={"content": "hi"}, headers=auth_headers
        )  # exhausts the bucket (429)

        # GET requests and conversation creation are not rate limited at all.
        assert client.get("/conversations", headers=auth_headers).status_code == 200
        assert client.post("/conversations", json={}, headers=auth_headers).status_code == 201
    finally:
        limiter.capacity_per_minute = original_capacity
        limiter.reset()
