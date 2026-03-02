import pytest
from unittest.mock import AsyncMock
from services.search_engine.recall.vector import VectorRecall


@pytest.fixture
def mock_vector_client():
    client = AsyncMock()
    client.search = AsyncMock(return_value=[(1, 0.1), (2, 0.3), (5, 0.5)])
    return client


async def test_recall_delegates_to_client(mock_vector_client):
    recall = VectorRecall(mock_vector_client)
    results = await recall.recall([0.1] * 1024, k=50)
    assert results == [(1, 0.1), (2, 0.3), (5, 0.5)]
    mock_vector_client.search.assert_called_once_with([0.1] * 1024, k=50)


async def test_recall_empty(mock_vector_client):
    mock_vector_client.search.return_value = []
    recall = VectorRecall(mock_vector_client)
    results = await recall.recall([0.1] * 1024)
    assert results == []


async def test_recall_default_k(mock_vector_client):
    recall = VectorRecall(mock_vector_client)
    await recall.recall([0.1] * 1024)
    mock_vector_client.search.assert_called_once_with([0.1] * 1024, k=100)
