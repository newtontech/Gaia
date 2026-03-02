# tests/services/test_search_engine/test_bm25_recall.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.search_engine.recall.bm25 import BM25Recall


@pytest.fixture
def mock_lance_store():
    store = MagicMock()
    store.fts_search = AsyncMock(return_value=[(1, 5.2), (3, 3.1), (7, 1.0)])
    return store


async def test_recall_delegates_to_fts(mock_lance_store):
    recall = BM25Recall(mock_lance_store)
    results = await recall.recall("superconductivity", k=50)
    assert results == [(1, 5.2), (3, 3.1), (7, 1.0)]
    mock_lance_store.fts_search.assert_called_once_with("superconductivity", k=50)


async def test_recall_empty(mock_lance_store):
    mock_lance_store.fts_search.return_value = []
    recall = BM25Recall(mock_lance_store)
    results = await recall.recall("nonexistent query")
    assert results == []


async def test_recall_default_k(mock_lance_store):
    recall = BM25Recall(mock_lance_store)
    await recall.recall("test query")
    mock_lance_store.fts_search.assert_called_once_with("test query", k=100)
