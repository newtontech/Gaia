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
    # graph is None in local mode
    if dep.storage.graph is None:
        resp = await c.get("/hyperedges/1")
        assert resp.status_code == 503


async def test_subgraph_with_direction_param(client):
    c, dep = client
    resp = await c.get("/nodes/1/subgraph?hops=2&direction=upstream&max_nodes=100")
    # 503 when graph store not available (no Neo4j), 200 otherwise
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        data = resp.json()
        assert "node_ids" in data
        assert "edge_ids" in data


async def test_subgraph_with_edge_types_param(client):
    c, dep = client
    resp = await c.get("/nodes/1/subgraph?hops=1&edge_types=abstraction,induction")
    assert resp.status_code in (200, 503)


async def test_subgraph_hydrated_with_params(client):
    c, dep = client
    resp = await c.get("/nodes/1/subgraph/hydrated?hops=1&direction=downstream&max_nodes=50")
    assert resp.status_code in (200, 503)


async def test_subgraph_invalid_direction(client):
    c, dep = client
    resp = await c.get("/nodes/1/subgraph?direction=sideways")
    # FastAPI should reject invalid Literal value with 422
    assert resp.status_code == 422
