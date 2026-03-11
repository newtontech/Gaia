"""Tests for StorageManager — unified storage facade."""

import pytest

from libs.storage_v2.config import StorageConfig
from libs.storage_v2.manager import StorageManager
from libs.storage_v2.models import Subgraph


@pytest.fixture
async def full_manager(tmp_path) -> StorageManager:
    """Manager with all three stores."""
    config = StorageConfig(
        lancedb_path=str(tmp_path / "lance"),
        graph_backend="kuzu",
        kuzu_path=str(tmp_path / "kuzu"),
    )
    mgr = StorageManager(config)
    await mgr.initialize()
    yield mgr
    await mgr.close()


@pytest.fixture
async def no_graph_manager(tmp_path) -> StorageManager:
    """Manager with graph_backend=none."""
    config = StorageConfig(
        lancedb_path=str(tmp_path / "lance"),
        graph_backend="none",
    )
    mgr = StorageManager(config)
    await mgr.initialize()
    yield mgr
    await mgr.close()


class TestInitialization:
    async def test_full_init(self, full_manager):
        assert full_manager.content_store is not None
        assert full_manager.graph_store is not None
        assert full_manager.vector_store is not None

    async def test_no_graph_init(self, no_graph_manager):
        assert no_graph_manager.content_store is not None
        assert no_graph_manager.graph_store is None
        assert no_graph_manager.vector_store is not None

    async def test_close_idempotent(self, full_manager):
        await full_manager.close()
        await full_manager.close()  # should not raise


class TestReadDelegation:
    async def test_get_closure_delegates(self, full_manager, packages, modules, closures, chains):
        pkg, mods = packages[0], [m for m in modules if m.package_id == packages[0].package_id]
        await full_manager.content_store.write_package(pkg, mods)
        await full_manager.content_store.write_closures(closures)
        c = await full_manager.get_closure(closures[0].closure_id)
        assert c is not None
        assert c.closure_id == closures[0].closure_id

    async def test_get_package_delegates(self, full_manager, packages, modules):
        pkg, mods = packages[0], [m for m in modules if m.package_id == packages[0].package_id]
        await full_manager.content_store.write_package(pkg, mods)
        p = await full_manager.get_package(pkg.package_id)
        assert p is not None
        assert p.package_id == pkg.package_id

    async def test_search_bm25_delegates(self, full_manager, packages, modules, closures):
        pkg, mods = packages[0], [m for m in modules if m.package_id == packages[0].package_id]
        await full_manager.content_store.write_package(pkg, mods)
        await full_manager.content_store.write_closures(closures)
        results = await full_manager.search_bm25("gravity", top_k=5)
        assert isinstance(results, list)


class TestDegradedMode:
    async def test_graph_none_returns_empty_subgraph(self, no_graph_manager):
        result = await no_graph_manager.get_neighbors("nonexistent")
        assert result == Subgraph()

    async def test_graph_none_search_topology_returns_empty(self, no_graph_manager):
        result = await no_graph_manager.search_topology(["nonexistent"])
        assert result == []

    async def test_vector_none_search_returns_empty(self, tmp_path):
        config = StorageConfig(
            lancedb_path=str(tmp_path / "lance"),
            graph_backend="none",
        )
        mgr = StorageManager(config)
        mgr.content_store = None  # skip init for this test
        mgr.vector_store = None
        result = await mgr.search_vector([0.1] * 8, top_k=5)
        assert result == []
