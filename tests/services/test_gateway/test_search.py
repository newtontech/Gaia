import pytest
from httpx import ASGITransport, AsyncClient
from services.gateway.app import create_app
from services.gateway.deps import Dependencies
from libs.storage import StorageConfig
from libs.models import Node
from libs.embedding import StubEmbeddingModel


@pytest.fixture
async def client(tmp_path):
    config = StorageConfig(lancedb_path=str(tmp_path / "lance"))
    dep = Dependencies(config)
    dep.initialize(config)
    # Force stub embedding so tests don't depend on .env / real API
    dep.search_engine._embedding_model = StubEmbeddingModel()
    app = create_app(dependencies=dep)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, dep


async def _seed_data(dep):
    embedding_model = StubEmbeddingModel()
    nodes = [
        Node(id=1, type="paper-extract", content="YH10 superconductivity at high pressure"),
        Node(id=2, type="paper-extract", content="LaH10 experiment under pressure"),
    ]
    await dep.storage.lance.save_nodes(nodes)
    # Generate embeddings via the same stub model used by the search engine
    embs = await embedding_model.embed([n.content for n in nodes])
    await dep.storage.vector.insert_batch([1, 2], embs)


async def test_search_nodes(client):
    c, dep = client
    await _seed_data(dep)
    resp = await c.post(
        "/search/nodes",
        json={"text": "superconductivity", "k": 10, "paths": ["vector", "bm25"]},
    )
    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)
    assert len(results) > 0, "Should find seeded superconductivity nodes"


async def test_search_nodes_empty(tmp_path):
    """Search with no data should return empty list."""
    config = StorageConfig(lancedb_path=str(tmp_path / "lance"))
    dep = Dependencies(config)
    dep.initialize(config)
    app = create_app(dependencies=dep)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/search/nodes",
            json={
                "text": "test",
                "k": 10,
                "paths": ["bm25"],
            },
        )
        assert resp.status_code == 200
