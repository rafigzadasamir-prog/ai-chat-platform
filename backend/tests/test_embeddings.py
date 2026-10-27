import numpy as np

from app.embeddings import HashingEmbedder


def test_hashing_embedder_output_shape() -> None:
    embedder = HashingEmbedder()
    vectors = embedder.embed(["hello world", "another sentence"])
    assert vectors.shape == (2, embedder.dim)


def test_hashing_embedder_vectors_are_unit_normalised() -> None:
    embedder = HashingEmbedder()
    vectors = embedder.embed(["some text with several words in it"])
    norm = np.linalg.norm(vectors[0])
    assert abs(norm - 1.0) < 1e-5


def test_hashing_embedder_is_deterministic() -> None:
    embedder = HashingEmbedder()
    first = embedder.embed(["repeatable text"])
    second = embedder.embed(["repeatable text"])
    assert np.allclose(first, second)


def test_hashing_embedder_similar_text_scores_higher_than_unrelated() -> None:
    embedder = HashingEmbedder()
    query = embedder.embed(["refund policy for purchases"])[0]
    related = embedder.embed(["our refund policy allows purchases to be returned"])[0]
    unrelated = embedder.embed(["the weather today is sunny and warm"])[0]

    assert float(query @ related) > float(query @ unrelated)


def test_hashing_embedder_handles_empty_string() -> None:
    embedder = HashingEmbedder()
    vectors = embedder.embed([""])
    assert vectors.shape == (1, embedder.dim)
    assert np.all(vectors == 0)
