"""LanceDB-backed implementation of ContentStore."""

from __future__ import annotations

import lancedb
import pyarrow as pa

from libs.storage_v2.content_store import ContentStore
from libs.storage_v2.models import (
    BeliefSnapshot,
    Chain,
    Closure,
    Module,
    Package,
    ProbabilityRecord,
    Resource,
    ResourceAttachment,
    ScoredClosure,
)

# ── PyArrow schemas ──

_PACKAGES_SCHEMA = pa.schema(
    [
        pa.field("package_id", pa.string()),
        pa.field("name", pa.string()),
        pa.field("version", pa.string()),
        pa.field("description", pa.string()),
        pa.field("modules", pa.string()),  # JSON list[str]
        pa.field("exports", pa.string()),  # JSON list[str]
        pa.field("submitter", pa.string()),
        pa.field("submitted_at", pa.string()),  # ISO datetime
        pa.field("status", pa.string()),
    ]
)

_MODULES_SCHEMA = pa.schema(
    [
        pa.field("module_id", pa.string()),
        pa.field("package_id", pa.string()),
        pa.field("name", pa.string()),
        pa.field("role", pa.string()),
        pa.field("imports", pa.string()),  # JSON list[ImportRef]
        pa.field("chain_ids", pa.string()),  # JSON list[str]
        pa.field("export_ids", pa.string()),  # JSON list[str]
    ]
)

_CLOSURES_SCHEMA = pa.schema(
    [
        pa.field("closure_id", pa.string()),
        pa.field("version", pa.int64()),
        pa.field("type", pa.string()),
        pa.field("content", pa.string()),
        pa.field("prior", pa.float64()),
        pa.field("keywords", pa.string()),  # JSON list[str]
        pa.field("source_package_id", pa.string()),
        pa.field("source_module_id", pa.string()),
        pa.field("created_at", pa.string()),  # ISO datetime
        pa.field("embedding", pa.string()),  # JSON list[float] or ""
    ]
)

_CHAINS_SCHEMA = pa.schema(
    [
        pa.field("chain_id", pa.string()),
        pa.field("module_id", pa.string()),
        pa.field("package_id", pa.string()),
        pa.field("type", pa.string()),
        pa.field("steps", pa.string()),  # JSON list[ChainStep]
    ]
)

_PROBABILITIES_SCHEMA = pa.schema(
    [
        pa.field("chain_id", pa.string()),
        pa.field("step_index", pa.int64()),
        pa.field("value", pa.float64()),
        pa.field("source", pa.string()),
        pa.field("source_detail", pa.string()),
        pa.field("recorded_at", pa.string()),  # ISO datetime
    ]
)

_BELIEF_HISTORY_SCHEMA = pa.schema(
    [
        pa.field("closure_id", pa.string()),
        pa.field("version", pa.int64()),
        pa.field("belief", pa.float64()),
        pa.field("bp_run_id", pa.string()),
        pa.field("computed_at", pa.string()),  # ISO datetime
    ]
)

_RESOURCES_SCHEMA = pa.schema(
    [
        pa.field("resource_id", pa.string()),
        pa.field("type", pa.string()),
        pa.field("format", pa.string()),
        pa.field("title", pa.string()),
        pa.field("description", pa.string()),
        pa.field("storage_backend", pa.string()),
        pa.field("storage_path", pa.string()),
        pa.field("size_bytes", pa.int64()),
        pa.field("checksum", pa.string()),
        pa.field("metadata", pa.string()),  # JSON dict
        pa.field("created_at", pa.string()),  # ISO datetime
        pa.field("source_package_id", pa.string()),
    ]
)

_RESOURCE_ATTACHMENTS_SCHEMA = pa.schema(
    [
        pa.field("resource_id", pa.string()),
        pa.field("target_type", pa.string()),
        pa.field("target_id", pa.string()),
        pa.field("role", pa.string()),
        pa.field("description", pa.string()),
    ]
)

_TABLE_SCHEMAS: dict[str, pa.Schema] = {
    "packages": _PACKAGES_SCHEMA,
    "modules": _MODULES_SCHEMA,
    "closures": _CLOSURES_SCHEMA,
    "chains": _CHAINS_SCHEMA,
    "probabilities": _PROBABILITIES_SCHEMA,
    "belief_history": _BELIEF_HISTORY_SCHEMA,
    "resources": _RESOURCES_SCHEMA,
    "resource_attachments": _RESOURCE_ATTACHMENTS_SCHEMA,
}


class LanceContentStore(ContentStore):
    """LanceDB-backed content store for Gaia v2 storage layer."""

    def __init__(self, db_path: str) -> None:
        self._db = lancedb.connect(db_path)
        self._fts_dirty = True

    # ── Schema setup ──

    async def initialize(self) -> None:
        """Create all required tables if they don't already exist."""
        existing = set(self._db.table_names())
        for table_name, schema in _TABLE_SCHEMAS.items():
            if table_name not in existing:
                self._db.create_table(table_name, schema=schema)

    # ── Write ──

    async def write_package(self, package: Package, modules: list[Module]) -> None:
        raise NotImplementedError

    async def write_closures(self, closures: list[Closure]) -> None:
        raise NotImplementedError

    async def write_chains(self, chains: list[Chain]) -> None:
        raise NotImplementedError

    async def write_probabilities(self, records: list[ProbabilityRecord]) -> None:
        raise NotImplementedError

    async def write_belief_snapshots(self, snapshots: list[BeliefSnapshot]) -> None:
        raise NotImplementedError

    async def write_resources(
        self, resources: list[Resource], attachments: list[ResourceAttachment]
    ) -> None:
        raise NotImplementedError

    # ── Read ──

    async def get_closure(self, closure_id: str, version: int | None = None) -> Closure | None:
        raise NotImplementedError

    async def get_closure_versions(self, closure_id: str) -> list[Closure]:
        raise NotImplementedError

    async def get_package(self, package_id: str) -> Package | None:
        raise NotImplementedError

    async def get_module(self, module_id: str) -> Module | None:
        raise NotImplementedError

    async def get_chains_by_module(self, module_id: str) -> list[Chain]:
        raise NotImplementedError

    async def get_probability_history(
        self, chain_id: str, step_index: int | None = None
    ) -> list[ProbabilityRecord]:
        raise NotImplementedError

    async def get_belief_history(self, closure_id: str) -> list[BeliefSnapshot]:
        raise NotImplementedError

    async def get_resources_for(self, target_type: str, target_id: str) -> list[Resource]:
        raise NotImplementedError

    # ── Search ──

    async def search_bm25(self, text: str, top_k: int) -> list[ScoredClosure]:
        raise NotImplementedError

    # ── BP bulk load ──

    async def list_closures(self) -> list[Closure]:
        raise NotImplementedError

    async def list_chains(self) -> list[Chain]:
        raise NotImplementedError
