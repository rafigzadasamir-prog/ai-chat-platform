"""Embedding backends for lightweight RAG grounding.

Mirrors the same "real provider + deterministic offline fallback" pattern
used for the LLM backend (see app/llm/): a real ``SentenceTransformerEmbedder``
for when the optional ``sentence-transformers`` extra is installed and a
model can actually be loaded, and a dependency-free ``HashingEmbedder`` that
is always available, fully deterministic and requires zero network access --
used by default and exclusively in the test suite.

Both backends implement the same interface: ``embed(texts) -> np.ndarray``
of shape (len(texts), dim), L2-normalised so that a dot product is a cosine
similarity.
"""

from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from typing import ClassVar

import numpy as np

from app.config import get_settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class Embedder(ABC):
    dim: ClassVar[int]

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray: ...


class HashingEmbedder(Embedder):
    """Deterministic, dependency-free bag-of-words hashing embedder.

    Each token is hashed into one of ``dim`` buckets with a signed count
    (the "hashing trick"), then the resulting vector is L2-normalised. This
    has no learned semantics, but it reliably ranks documents that share
    vocabulary with the query above those that don't -- enough to
    demonstrate real retrieval-augmented grounding fully offline.
    """

    dim = 256

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in _TOKEN_RE.findall(text.lower()):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                bucket = int.from_bytes(digest[:4], "big") % self.dim
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vectors[row, bucket] += sign
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms


class SentenceTransformerEmbedder(Embedder):
    """Real sentence embeddings via the optional sentence-transformers extra."""

    dim = 384  # all-MiniLM-L6-v2 output size

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return np.asarray(vectors, dtype=np.float32)


_embedder_instance: Embedder | None = None


def get_embedder() -> Embedder:
    """Resolve the configured embedding backend, with graceful fallback.

    - "hashing": always the dependency-free embedder (used by the test suite).
    - "sentence-transformers": require the real backend; raises if unavailable.
    - "auto" (default): try the real backend, silently fall back to hashing
      if the package is missing or the model can't be loaded (no cached
      weights / no network).
    """
    global _embedder_instance
    if _embedder_instance is not None:
        return _embedder_instance

    backend = get_settings().embeddings_backend
    if backend == "hashing":
        _embedder_instance = HashingEmbedder()
    elif backend == "sentence-transformers":
        _embedder_instance = SentenceTransformerEmbedder()
    else:  # auto
        try:
            _embedder_instance = SentenceTransformerEmbedder()
        except Exception:
            _embedder_instance = HashingEmbedder()
    return _embedder_instance


def reset_embedder_cache() -> None:
    """Testing hook: force re-resolution of the embedder backend."""
    global _embedder_instance
    _embedder_instance = None
