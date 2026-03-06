import pytest
from httpx import ASGITransport, AsyncClient
from services.gateway.app import create_app
from services.gateway.deps import Dependencies
from libs.storage import StorageConfig
from libs.models import Node


@pytest.fixture
async def client(tmp_path):
    config = StorageConfig(lancedb_path=str(tmp_path / "lance"))
    dep = Dependencies(config)
    dep.initialize(config)
    app = create_app(dependencies=dep)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, dep


async def _seed_node(dep, node_id=1, content="test node"):
    node = Node(id=node_id, type="paper-extract", content=content)
    await dep.storage.lance.save_nodes([node])


async def test_get_node(client):
    c, dep = client
    await _seed_node(dep)
    resp = await c.get("/nodes/1")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1


async def test_get_node_not_found(client):
    c, dep = client
    resp = await c.get("/nodes/999")
    assert resp.status_code == 404


async def test_get_hyperedge_no_graph(client):
    c, dep = client
    dep.storage.graph = None
    resp = await c.get("/hyperedges/1")
    assert resp.status_code == 503


async def test_subgraph_no_graph_returns_503(client):
    """Subgraph requires graph store; returns 503 without it."""
    c, dep = client
    dep.storage.graph = None
    resp = await c.get("/nodes/1/subgraph?hops=2&direction=upstream&max_nodes=100")
    assert resp.status_code == 503


async def test_subgraph_hydrated_no_graph_returns_503(client):
    c, dep = client
    dep.storage.graph = None
    resp = await c.get("/nodes/1/subgraph/hydrated?hops=1&direction=downstream&max_nodes=50")
    assert resp.status_code == 503


async def test_subgraph_invalid_direction(client):
    c, dep = client
    resp = await c.get("/nodes/1/subgraph?direction=sideways")
    # FastAPI should reject invalid Literal value with 422
    assert resp.status_code == 422


async def test_list_nodes_empty(client):
    """GET /nodes returns empty paginated result when no data."""
    c, dep = client
    resp = await c.get("/nodes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 50


async def test_list_nodes_with_data(client):
    """GET /nodes returns seeded nodes with pagination."""
    c, dep = client
    await _seed_node(dep, 1, "node A")
    await _seed_node(dep, 2, "node B")
    resp = await c.get("/nodes?page=1&size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


async def test_list_nodes_type_filter(client):
    """GET /nodes?type=paper-extract filters by type."""
    c, dep = client
    await _seed_node(dep, 1, "node A")
    resp = await c.get("/nodes?type=paper-extract")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["type"] == "paper-extract"


async def test_list_hyperedges_no_graph(client):
    """GET /hyperedges returns 503 when graph store unavailable."""
    c, dep = client
    dep.storage.graph = None
    resp = await c.get("/hyperedges")
    assert resp.status_code == 503


async def test_contradictions_no_graph(client):
    """GET /contradictions returns 503 when graph store unavailable."""
    c, dep = client
    dep.storage.graph = None
    resp = await c.get("/contradictions")
    assert resp.status_code == 503


async def test_stats(client):
    """GET /stats returns system statistics."""
    c, dep = client
    await _seed_node(dep, 1, "test")
    resp = await c.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["node_count"] >= 1
    assert "graph_available" in data
    assert "edge_count" in data
    assert "node_types" in data
