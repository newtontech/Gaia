"""Shared test fixtures — real storage backends seeded with fixture data."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from libs.models import HyperEdge, Node
from libs.storage import StorageConfig, StorageManager

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture_nodes() -> list[Node]:
    """Load nodes from tests/fixtures/nodes.json."""
    with open(FIXTURES_DIR / "nodes.json") as f:
        raw = json.load(f)
    return [Node.model_validate(n) for n in raw]


def load_fixture_edges() -> list[HyperEdge]:
    """Load edges from tests/fixtures/edges.json."""
    with open(FIXTURES_DIR / "edges.json") as f:
        raw = json.load(f)
    return [HyperEdge.model_validate(e) for e in raw]


def load_fixture_embeddings() -> dict[int, list[float]] | None:
    """Load embeddings from tests/fixtures/embeddings.json if it exists."""
    path = FIXTURES_DIR / "embeddings.json"
    if not path.exists():
        return None
    with open(path) as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}


@pytest.fixture
async def storage(tmp_path: Path) -> StorageManager:
    """Real StorageManager seeded with fixture data (LanceDB + vector, no Neo4j)."""
    config = StorageConfig(
        deployment_mode="local",
        lancedb_path=str(tmp_path / "lance"),
        neo4j_password="",
    )
    manager = StorageManager(config)

    # Seed nodes
    nodes = load_fixture_nodes()
    await manager.lance.save_nodes(nodes)

    # Seed edges (Neo4j only if available and reachable)
    if manager.graph:
        try:
            edges = load_fixture_edges()
            for edge in edges:
                await manager.graph.create_hyperedge(edge)
        except Exception:
            manager.graph = None  # degrade gracefully

    # Seed embeddings (vector index)
    embeddings = load_fixture_embeddings()
    if embeddings:
        node_ids = list(embeddings.keys())
        vectors = list(embeddings.values())
        await manager.vector.insert_batch(node_ids, vectors)

    yield manager
    await manager.close()


@pytest.fixture
async def storage_empty(tmp_path: Path) -> StorageManager:
    """Empty real StorageManager — no fixture data loaded."""
    config = StorageConfig(
        deployment_mode="local",
        lancedb_path=str(tmp_path / "lance"),
        neo4j_password="",
    )
    manager = StorageManager(config)
    yield manager
    await manager.close()
