"""Centralised application configuration.

Everything that varies between local development, CI and a hypothetical
production deployment is read from the environment (optionally via a
``.env`` file) so that, for example, swapping SQLite for Postgres is a
one-line change to ``DATABASE_URL`` with no code changes required.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Chat Platform"

    # SQLAlchemy accepts any dialect URL here (sqlite://, postgresql+psycopg://, ...).
    # SQLite is the default so the project runs with zero external services.
    database_url: str = "sqlite:///./ai_chat_platform.db"

    # JWT / auth
    secret_key: str = "dev-secret-key-change-me-in-production-please-32-bytes-min"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # AI backend. When anthropic_api_key is unset (or empty), the app
    # transparently falls back to the deterministic OfflineLLM so the whole
    # stack is runnable and testable without network access or secrets.
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    # Embeddings backend for RAG grounding. "auto" tries sentence-transformers
    # (if installed and a model can be loaded) and falls back to the
    # dependency-free hashing embedder otherwise. Tests force "hashing" so
    # they never touch the network.
    embeddings_backend: Literal["auto", "hashing", "sentence-transformers"] = "auto"

    # Rate limiting: messages allowed per user per 60 seconds.
    rate_limit_messages_per_minute: int = 20

    # CORS: comma separated list of allowed origins for the frontend.
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
