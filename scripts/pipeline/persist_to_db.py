#!/usr/bin/env python3
"""Persist Graph IR outputs to LanceDB + Graph DB via StorageManager.

Reads per-package Graph IR outputs (local_canonical_graph.json, local_parameterization.json,
local_beliefs.json) and the global graph, writes everything to storage. Saves local JSON
backups for debugging.

Usage:
    python scripts/pipeline/persist_to_db.py \
        --packages-dir output_typst \
        --global-graph-dir global_graph \
        --db-path ./data/lancedb/gaia \
        --graph-backend kuzu
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from libs.global_graph.models import (
    CanonicalBinding as GGCanonicalBinding,
    GlobalCanonicalNode as GGGlobalCanonicalNode,
    GlobalGraph,
    GlobalInferenceState as GGInferenceState,
)
from libs.global_graph.serialize import load_global_graph
from libs.graph_ir.models import LocalCanonicalGraph, LocalParameterization
from libs.graph_ir.storage_converter import convert_graph_ir_to_storage
from libs.storage import models as storage
from libs.storage.config import StorageConfig
from libs.storage.manager import StorageManager

logger = logging.getLogger(__name__)


# ── Global graph model conversion ──


def _convert_global_canonical_node(
    gg_node: GGGlobalCanonicalNode,
) -> storage.GlobalCanonicalNode:
    """Convert global_graph GlobalCanonicalNode to storage GlobalCanonicalNode."""
    return storage.GlobalCanonicalNode(
        global_canonical_id=gg_node.global_canonical_id,
        knowledge_type=gg_node.knowledge_type,
        kind=gg_node.kind,
        representative_content=gg_node.representative_content,
        parameters=[
            storage.Parameter(name=p.name, constraint=p.constraint) for p in gg_node.parameters
        ],
        member_local_nodes=[
            storage.LocalCanonicalRef(
                package=m.package, version=m.version, local_canonical_id=m.local_canonical_id
            )
            for m in gg_node.member_local_nodes
        ],
        provenance=[
            storage.PackageRef(package=p.package, version=p.version) for p in gg_node.provenance
        ],
        metadata=gg_node.metadata,
    )


def _convert_canonical_binding(
    gg_binding: GGCanonicalBinding,
    now: datetime,
) -> storage.CanonicalBinding:
    """Convert global_graph CanonicalBinding to storage CanonicalBinding.

    Storage model requires decided_at (datetime) which global_graph model lacks.
    """
    return storage.CanonicalBinding(
        package=gg_binding.package,
        version=gg_binding.version,
        local_graph_hash=gg_binding.local_graph_hash,
        local_canonical_id=gg_binding.local_canonical_id,
        decision=gg_binding.decision,
        global_canonical_id=gg_binding.global_canonical_id,
        decided_at=now,
        decided_by=gg_binding.decided_by,
        reason=gg_binding.reason,
    )


def _convert_inference_state(
    gg_state: GGInferenceState,
) -> storage.GlobalInferenceState:
    """Convert global_graph GlobalInferenceState to storage GlobalInferenceState.

    Storage model requires updated_at as datetime; global_graph uses str.
    """
    if gg_state.updated_at:
        try:
            updated_at = datetime.fromisoformat(gg_state.updated_at)
        except (ValueError, TypeError):
            updated_at = datetime.now(UTC)
    else:
        updated_at = datetime.now(UTC)

    factor_params = {
        fid: storage.FactorParams(conditional_probability=fp.conditional_probability)
        for fid, fp in gg_state.factor_parameters.items()
    }

    return storage.GlobalInferenceState(
        graph_hash=gg_state.graph_hash,
        node_priors=gg_state.node_priors,
        factor_parameters=factor_params,
        node_beliefs=gg_state.node_beliefs,
        updated_at=updated_at,
    )


def _convert_global_factors(
    global_graph: GlobalGraph,
) -> list[storage.FactorNode]:
    """Convert global graph factor nodes to storage FactorNode models."""
    factors: list[storage.FactorNode] = []
    for f in global_graph.factor_nodes:
        source_ref = None
        if f.source_ref:
            source_ref = storage.SourceRef(
                package=f.source_ref.package,
                version=f.source_ref.version,
                module=f.source_ref.module,
                knowledge_name=f.source_ref.knowledge_name,
            )
        factors.append(
            storage.FactorNode(
                factor_id=f.factor_id,
                type=f.type,
                premises=list(f.premises),
                contexts=list(f.contexts),
                conclusion=f.conclusion,
                package_id=f.package_id,
                source_ref=source_ref,
                metadata=f.metadata,
            )
        )
    return factors


# ── JSON backup helpers ──


def _save_backup(backup_dir: Path, data: dict, filename: str) -> None:
    """Write a JSON backup file."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / filename).write_text(
        json.dumps(data, ensure_ascii=False, default=str, sort_keys=True, indent=2)
    )


def _save_package_backups(pkg_dir: Path, ingest_data) -> None:
    """Save local JSON backups for a package's storage objects."""
    backup_dir = pkg_dir / "graph_ir" / "storage_backup"
    _save_backup(
        backup_dir,
        ingest_data.package.model_dump(mode="json"),
        "package.json",
    )
    _save_backup(
        backup_dir,
        [k.model_dump(mode="json") for k in ingest_data.knowledge_items],
        "knowledge.json",
    )
    _save_backup(
        backup_dir,
        [f.model_dump(mode="json") for f in ingest_data.factors],
        "factors.json",
    )
    _save_backup(
        backup_dir,
        [m.model_dump(mode="json") for m in ingest_data.modules],
        "modules.json",
    )


# ── Package discovery ──


def _discover_packages(packages_dir: Path) -> list[Path]:
    """Find all package directories that have graph_ir/local_canonical_graph.json."""
    found: list[Path] = []
    if not packages_dir.is_dir():
        return found
    for sub in sorted(packages_dir.iterdir()):
        if sub.is_dir() and (sub / "graph_ir" / "local_canonical_graph.json").exists():
            found.append(sub)
    return found


def _load_local_graph(pkg_dir: Path) -> LocalCanonicalGraph:
    """Load local canonical graph from a package directory."""
    path = pkg_dir / "graph_ir" / "local_canonical_graph.json"
    return LocalCanonicalGraph.model_validate_json(path.read_text())


def _load_local_params(pkg_dir: Path) -> LocalParameterization:
    """Load local parameterization from a package directory."""
    path = pkg_dir / "graph_ir" / "local_parameterization.json"
    if not path.exists():
        return LocalParameterization(package="", version="")
    return LocalParameterization.model_validate_json(path.read_text())


def _load_local_beliefs(pkg_dir: Path) -> dict[str, float] | None:
    """Load local beliefs if they exist."""
    path = pkg_dir / "graph_ir" / "local_beliefs.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    # local_beliefs.json stores node_beliefs as a dict
    if isinstance(data, dict):
        return data.get("node_beliefs", data)
    return None


# ── Main pipeline ──


async def persist_packages(
    packages_dir: Path,
    mgr: StorageManager,
) -> int:
    """Persist all per-package Graph IR to storage. Returns count of packages persisted."""
    pkg_dirs = _discover_packages(packages_dir)
    if not pkg_dirs:
        logger.warning("No packages with graph_ir/ found in %s", packages_dir)
        return 0

    count = 0
    for pkg_dir in pkg_dirs:
        pkg_name = pkg_dir.name
        logger.info("Persisting package: %s", pkg_name)

        lcg = _load_local_graph(pkg_dir)
        params = _load_local_params(pkg_dir)
        beliefs = _load_local_beliefs(pkg_dir)

        ingest_data = convert_graph_ir_to_storage(lcg, params, beliefs)

        # Save local backups before writing to DB
        _save_package_backups(pkg_dir, ingest_data)

        # Write to storage
        await mgr.ingest_package(
            package=ingest_data.package,
            modules=ingest_data.modules,
            knowledge_items=ingest_data.knowledge_items,
            chains=ingest_data.chains,
            factors=ingest_data.factors,
        )

        # Write beliefs if present
        if ingest_data.belief_snapshots:
            await mgr.write_beliefs(ingest_data.belief_snapshots)

        count += 1
        logger.info(
            "  -> %d knowledge, %d factors, %d beliefs",
            len(ingest_data.knowledge_items),
            len(ingest_data.factors),
            len(ingest_data.belief_snapshots),
        )

    return count


async def persist_global_graph(
    global_graph_dir: Path,
    mgr: StorageManager,
) -> bool:
    """Persist global graph to storage. Returns True if persisted."""
    gg_path = global_graph_dir / "global_graph.json"
    if not gg_path.exists():
        logger.info("No global_graph.json found at %s — skipping", gg_path)
        return False

    logger.info("Loading global graph from %s", gg_path)
    global_graph = load_global_graph(gg_path)

    now = datetime.now(UTC)

    # Convert models
    storage_nodes = [_convert_global_canonical_node(n) for n in global_graph.knowledge_nodes]
    storage_bindings = [_convert_canonical_binding(b, now) for b in global_graph.bindings]
    storage_state = _convert_inference_state(global_graph.inference_state)
    storage_factors = _convert_global_factors(global_graph)

    logger.info(
        "Global graph: %d nodes, %d bindings, %d factors",
        len(storage_nodes),
        len(storage_bindings),
        len(storage_factors),
    )

    # Write canonical bindings + global nodes
    if storage_bindings or storage_nodes:
        await mgr.write_canonical_bindings(storage_bindings, storage_nodes)

    # Write global factors
    if storage_factors:
        await mgr.write_factors(storage_factors)

    # Write inference state
    if storage_state.graph_hash:
        await mgr.update_inference_state(storage_state)

    # Save backup
    backup_dir = global_graph_dir / "storage_backup"
    _save_backup(
        backup_dir,
        [n.model_dump(mode="json") for n in storage_nodes],
        "global_nodes.json",
    )
    _save_backup(
        backup_dir,
        [b.model_dump(mode="json") for b in storage_bindings],
        "bindings.json",
    )
    _save_backup(
        backup_dir,
        storage_state.model_dump(mode="json"),
        "inference_state.json",
    )

    return True


async def main(args: argparse.Namespace) -> None:
    """Run the persist-to-db pipeline."""
    config = StorageConfig(
        lancedb_path=args.db_path,
        graph_backend=args.graph_backend,
    )

    mgr = StorageManager(config)
    await mgr.initialize()

    try:
        # Per-package persistence
        pkg_count = await persist_packages(Path(args.packages_dir), mgr)
        logger.info("Persisted %d packages", pkg_count)

        # Global graph persistence
        if args.global_graph_dir:
            gg_dir = Path(args.global_graph_dir)
            persisted = await persist_global_graph(gg_dir, mgr)
            if persisted:
                logger.info("Global graph persisted successfully")
        else:
            logger.info("No --global-graph-dir specified — skipping global graph")

    finally:
        await mgr.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Persist Graph IR outputs to LanceDB + Graph DB via StorageManager."
    )
    parser.add_argument(
        "--packages-dir",
        required=True,
        help="Directory containing packages with graph_ir/ subdirs.",
    )
    parser.add_argument(
        "--global-graph-dir",
        default=None,
        help="Directory containing global_graph.json (optional).",
    )
    parser.add_argument(
        "--db-path",
        default="./data/lancedb/gaia",
        help="LanceDB path (default: ./data/lancedb/gaia).",
    )
    parser.add_argument(
        "--graph-backend",
        choices=["kuzu", "neo4j", "none"],
        default="none",
        help="Graph backend: kuzu, neo4j, or none (default: none).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(main(parse_args()))
