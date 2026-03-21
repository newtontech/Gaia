#!/usr/bin/env python3
"""Run belief propagation on the global graph stored in DB.

Reads factors + inference state from StorageManager, runs loopy BP,
writes updated beliefs back to DB. Saves a local JSON backup.

Usage:
    python scripts/pipeline/run_global_bp_db.py \
        --db-path ./data/lancedb/gaia \
        --graph-backend none \
        --damping 0.3 \
        --max-iter 100 \
        --backup-path output/global_beliefs.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from libs.inference.bp import BeliefPropagation
from libs.inference.factor_graph import FactorGraph
from libs.storage import models as storage
from libs.storage.config import StorageConfig
from libs.storage.manager import StorageManager

logger = logging.getLogger(__name__)


def _build_factor_graph(
    factors: list[storage.FactorNode],
    global_nodes: list[storage.GlobalCanonicalNode],
    state: storage.GlobalInferenceState | None,
) -> tuple[FactorGraph, dict[int, str], dict[str, float]]:
    """Build a FactorGraph from DB factors, nodes, and priors.

    Returns the FactorGraph, int->gcn_id mapping, and the node_priors used.
    """
    fg = FactorGraph()
    id_to_int: dict[str, int] = {}
    int_to_id: dict[int, str] = {}

    node_priors: dict[str, float] = state.node_priors if state else {}
    factor_params: dict[str, storage.FactorParams] = state.factor_parameters if state else {}

    # Add variable nodes
    for i, node in enumerate(global_nodes):
        gcn_id = node.global_canonical_id
        id_to_int[gcn_id] = i
        int_to_id[i] = gcn_id
        prior = node_priors.get(gcn_id, 0.5)
        fg.add_variable(i, prior)

    # Add factor nodes
    for fi, factor in enumerate(factors):
        premises_int = [id_to_int[p] for p in factor.premises if p in id_to_int]
        if not premises_int:
            continue

        fp = factor_params.get(factor.factor_id)
        prob = fp.conditional_probability if fp else 0.5

        if factor.type in ("contradiction", "equivalence"):
            fg.add_factor(fi, premises_int, [], prob, factor.type)
        else:
            conclusion_int = id_to_int.get(factor.conclusion) if factor.conclusion else None
            if conclusion_int is not None:
                fg.add_factor(fi, premises_int, [conclusion_int], prob, factor.type)

    return fg, int_to_id, node_priors


async def run_global_bp_db(
    db_path: str,
    graph_backend: str,
    damping: float = 0.3,
    max_iter: int = 100,
    backup_path: str | None = None,
) -> dict[str, float]:
    """Load graph from DB, run BP, write beliefs back. Returns belief map."""
    config = StorageConfig(
        lancedb_path=db_path,
        graph_backend=graph_backend,
    )
    mgr = StorageManager(config)
    await mgr.initialize()

    try:
        # Read from DB
        factors, state = await mgr.load_global_factor_graph()
        global_nodes = await mgr.list_global_nodes()

        if not global_nodes:
            logger.info("No global nodes in DB, nothing to do.")
            return {}

        logger.info(
            "Loaded from DB: %d global nodes, %d factors, state=%s",
            len(global_nodes),
            len(factors),
            "present" if state else "absent",
        )

        # Build factor graph
        fg, int_to_id, node_priors = _build_factor_graph(factors, global_nodes, state)

        # Run BP
        bp = BeliefPropagation(damping=damping, max_iterations=max_iter)
        beliefs = bp.run(fg)

        # Map int IDs back to string IDs
        belief_map = {int_to_id[k]: round(v, 6) for k, v in beliefs.items()}

        # Log results
        for node in global_nodes:
            gcn_id = node.global_canonical_id
            label = node.representative_content[:60] if node.representative_content else gcn_id[:16]
            prior = node_priors.get(gcn_id, 0.5)
            b = belief_map.get(gcn_id, prior)
            delta = b - prior
            arrow = "^" if delta > 0.01 else "v" if delta < -0.01 else "="
            logger.info(
                "  %s %-60s prior=%.3f -> belief=%.3f (%+.3f)",
                arrow,
                label,
                prior,
                b,
                delta,
            )

        # Update inference state in DB
        now = datetime.now(UTC)
        bp_run_id = str(uuid.uuid4())

        if state:
            state.node_beliefs = belief_map
            state.updated_at = now
        else:
            state = storage.GlobalInferenceState(
                graph_hash="",
                node_priors=node_priors,
                factor_parameters={},
                node_beliefs=belief_map,
                updated_at=now,
            )

        await mgr.update_inference_state(state)
        logger.info("Updated inference state in DB with %d beliefs", len(belief_map))

        # Write BeliefSnapshot entries for each node
        snapshots: list[storage.BeliefSnapshot] = []
        for node in global_nodes:
            gcn_id = node.global_canonical_id
            b = belief_map.get(gcn_id)
            if b is None:
                continue
            # Use gcn_id as knowledge_id, version=1 for global beliefs
            snapshots.append(
                storage.BeliefSnapshot(
                    knowledge_id=gcn_id,
                    version=1,
                    belief=b,
                    bp_run_id=bp_run_id,
                    computed_at=now,
                )
            )

        if snapshots:
            await mgr.write_beliefs(snapshots)
            logger.info("Wrote %d belief snapshots to DB", len(snapshots))

        # Save local JSON backup
        if backup_path:
            backup = Path(backup_path)
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup_data = {
                "bp_run_id": bp_run_id,
                "computed_at": now.isoformat(),
                "damping": damping,
                "max_iterations": max_iter,
                "num_nodes": len(global_nodes),
                "num_factors": len(factors),
                "node_beliefs": belief_map,
                "node_priors": node_priors,
            }
            backup.write_text(json.dumps(backup_data, ensure_ascii=False, sort_keys=True, indent=2))
            logger.info("Saved beliefs backup to %s", backup)

        return belief_map

    finally:
        await mgr.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run global BP from DB: read factors + priors, run BP, write beliefs back."
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
    parser.add_argument(
        "--damping",
        type=float,
        default=0.3,
        help="BP damping factor (default: 0.3).",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=100,
        help="Max BP iterations (default: 100).",
    )
    parser.add_argument(
        "--backup-path",
        default="output/global_beliefs.json",
        help="Path for local JSON backup of beliefs (default: output/global_beliefs.json).",
    )
    return parser.parse_args(argv)


async def main(args: argparse.Namespace) -> None:
    await run_global_bp_db(
        db_path=args.db_path,
        graph_backend=args.graph_backend,
        damping=args.damping,
        max_iter=args.max_iter,
        backup_path=args.backup_path,
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(main(parse_args()))
