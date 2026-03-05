# tests/services/test_search_engine/test_vector_recall.py
"""VectorRecall tests — real LanceDB vector index instead of mocks."""

import pytest

from libs.embedding import StubEmbeddingModel
from services.search_engine.recall.vector import VectorRecall

_embedding_model = StubEmbeddingModel()


@pytest.fixture
async def vector(storage):
    return VectorRecall(storage.vector)


async def test_recall_finds_similar_vectors(vector):
    """Vector recall should find results when embeddings are loaded."""
    # Generate a query embedding matching what conftest seeded
    query = (await _embedding_model.embed(["superconductor"]))[0]
    results = await vector.recall(query, k=5)
    assert len(results) > 0
    for nid, _ in results:
        assert isinstance(nid, int)


async def test_recall_empty_when_no_embeddings(storage_empty):
    """VectorRecall on empty storage returns empty list."""
    recall = VectorRecall(storage_empty.vector)
    query = (await _embedding_model.embed(["test"]))[0]
    results = await recall.recall(query, k=10)
    assert results == []


async def test_recall_respects_k(vector):
    """Results should be limited to k."""
    query = (await _embedding_model.embed(["superconductor"]))[0]
    results = await vector.recall(query, k=3)
    assert len(results) <= 3
