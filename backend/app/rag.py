"""Chunking, indexing and retrieval for per-conversation document grounding.

Documents attached to a conversation are split into overlapping character
chunks, embedded, and stored as rows in the ``document_chunks`` table. At
query time we load that conversation's chunks, stack their stored embedding
vectors into a small NumPy matrix and rank by cosine similarity -- a "plain
NumPy index" scoped to one conversation, with no external vector database.
"""

from __future__ import annotations

import numpy as np
from sqlalchemy.orm import Session

from app.embeddings import get_embedder
from app.models import DocumentChunk

CHUNK_SIZE = 400
CHUNK_OVERLAP = 60


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks on whitespace boundaries where possible."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            # Prefer breaking on whitespace near the boundary for readability.
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def index_document(db: Session, conversation_id: int, document_name: str, content: str) -> int:
    """Chunk, embed and persist a document for a conversation. Returns chunk count."""
    chunks = chunk_text(content)
    if not chunks:
        return 0

    embedder = get_embedder()
    vectors = embedder.embed(chunks)

    for idx, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
        db.add(
            DocumentChunk(
                conversation_id=conversation_id,
                document_name=document_name,
                chunk_index=idx,
                text=chunk,
                embedding=vector.tolist(),
            )
        )
    db.commit()
    return len(chunks)


def retrieve_context(
    db: Session, conversation_id: int, query: str, top_k: int = 3, min_score: float = 0.05
) -> list[str]:
    """Return the top-k most relevant stored chunks for a query, best first."""
    rows = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.conversation_id == conversation_id)
        .all()
    )
    if not rows:
        return []

    embedder = get_embedder()
    query_vector = embedder.embed([query])[0]

    matrix = np.array([row.embedding for row in rows], dtype=np.float32)
    scores = matrix @ query_vector  # vectors are pre-normalised -> dot product = cosine similarity

    ranked_indices = np.argsort(-scores)[:top_k]
    return [rows[i].text for i in ranked_indices if scores[i] >= min_score]
