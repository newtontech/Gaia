"""gaia compile --readme: generate README.md from compiled IR."""

from __future__ import annotations

from collections import defaultdict


def topo_layers(ir: dict) -> dict[str, int]:
    """Assign each knowledge ID a topological layer (0 = no incoming edges)."""
    all_ids = {k["id"] for k in ir["knowledges"]}
    # Map conclusion → set of premise IDs (incoming edges)
    incoming: dict[str, set[str]] = defaultdict(set)
    for s in ir.get("strategies", []):
        conclusion = s.get("conclusion")
        if conclusion and conclusion in all_ids:
            for p in s.get("premises", []):
                if p in all_ids:
                    incoming[conclusion].add(p)
    for o in ir.get("operators", []):
        conclusion = o.get("conclusion")
        if conclusion and conclusion in all_ids:
            for v in o.get("variables", []):
                if v in all_ids:
                    incoming[conclusion].add(v)

    layers: dict[str, int] = {}
    remaining = set(all_ids)

    layer = 0
    while remaining:
        # Nodes whose all dependencies are already assigned
        ready = {
            nid
            for nid in remaining
            if not (incoming.get(nid, set()) - set(layers.keys()))
        }
        if not ready:
            # Cycle — assign remaining to current layer
            ready = remaining
        for nid in ready:
            layers[nid] = layer
        remaining -= ready
        layer += 1

    return layers
