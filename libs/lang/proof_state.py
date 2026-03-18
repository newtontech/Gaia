"""Proof state analysis for Gaia Language v3 packages.

Analyzes a loaded Typst graph to determine which declarations are
established (have reasoning factors or are relation types), which are
axioms (settings/observations), which are holes (claims used as premises
without proofs), and which are open questions.
"""

from __future__ import annotations

NO_PROOF_TYPES = {"setting", "observation", "question"}
RELATION_TYPES = {"contradiction", "equivalence"}


def analyze_proof_state(graph: dict) -> dict:
    """Analyze proof state of a loaded Typst package graph.

    Args:
        graph: Dict from load_typst_package() with nodes, factors,
               constraints.

    Returns:
        Dict with keys: established, axioms, holes, questions, report.
    """
    nodes = {n["name"]: n for n in graph.get("nodes", [])}

    # Names that are conclusions of reasoning factors (established)
    proven_names: set[str] = set()
    for factor in graph.get("factors", []):
        if factor.get("type") == "reasoning":
            proven_names.add(factor["conclusion"])

    # Names used as premises across all factors
    used_as_premise: set[str] = set()
    for factor in graph.get("factors", []):
        for p in factor.get("premise", []):
            used_as_premise.add(p)

    established: list[dict] = []
    axioms: list[dict] = []
    holes: list[dict] = []
    questions: list[dict] = []

    for name, node in nodes.items():
        node_type = node.get("type", "")

        if node_type == "question":
            questions.append(node)
        elif node_type in ("setting", "observation"):
            axioms.append(node)
        elif node_type in RELATION_TYPES:
            # claim_relation nodes are always established
            established.append(node)
        elif name in proven_names:
            established.append(node)
        elif name in used_as_premise:
            holes.append(node)
        # else: standalone claim, not used — could warn

    report = _format_report(established, axioms, holes, questions)

    return {
        "established": established,
        "axioms": axioms,
        "holes": holes,
        "questions": questions,
        "report": report,
    }


def _format_report(
    established: list[dict],
    axioms: list[dict],
    holes: list[dict],
    questions: list[dict],
) -> str:
    lines: list[str] = []

    if established:
        lines.append("\u2713 established:")
        for d in established:
            lines.append(f"  {d['name']}")

    if axioms:
        lines.append("")
        lines.append("\u25cb axioms (no proof needed):")
        for d in axioms:
            lines.append(f"  {d['name']}  ({d.get('type', '')})")

    if holes:
        lines.append("")
        lines.append("? holes:")
        for d in holes:
            lines.append(f"  {d['name']}  (claim, used as premise, no proof)")

    if questions:
        lines.append("")
        lines.append("? questions:")
        for d in questions:
            lines.append(f"  {d['name']}  (open)")

    return "\n".join(lines)
