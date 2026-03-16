"""Load a Typst-based Gaia package and extract the knowledge graph as JSON."""

from __future__ import annotations

import json
from pathlib import Path

import typst


def _flatten_content(node: dict | str | list) -> str:
    """Recursively flatten a Typst content tree to plain text."""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(_flatten_content(child) for child in node)
    if isinstance(node, dict):
        func = node.get("func", "")
        if func == "text":
            return node.get("text", "")
        if func == "space":
            return " "
        if func == "parbreak":
            return "\n\n"
        if func == "linebreak":
            return "\n"
        if func == "smartquote":
            return '"'
        children = node.get("children", [])
        if children:
            return "".join(_flatten_content(c) for c in children)
        body = node.get("body")
        if body:
            return _flatten_content(body)
    return ""


def load_typst_package(pkg_path: Path) -> dict:
    """Compile a Typst package and extract the knowledge graph via metadata query.

    Args:
        pkg_path: Path to directory containing typst.toml and lib.typ.

    Returns:
        Dict with keys: nodes, factors, refs, module, exports.
        Node content is flattened to plain text strings.
    """
    pkg_path = Path(pkg_path)
    entrypoint = pkg_path / "lib.typ"
    if not entrypoint.exists():
        raise FileNotFoundError(f"No lib.typ found in {pkg_path}")

    # Find repository root by walking up to find pyproject.toml
    root = pkg_path.resolve()
    while root != root.parent:
        if (root / "pyproject.toml").exists():
            break
        root = root.parent

    raw = typst.query(str(entrypoint), "<gaia-graph>", field="value", one=True, root=str(root))
    data = json.loads(raw) if isinstance(raw, str) else raw

    # Flatten content in nodes
    for node in data.get("nodes", []):
        if isinstance(node.get("content"), dict):
            node["content"] = _flatten_content(node["content"]).strip()
        # Normalize ctx -> context key for downstream consumers
        if "ctx" in node:
            node["context"] = node.pop("ctx")

    # Normalize ctx -> context in factors
    for factor in data.get("factors", []):
        if "ctx" in factor:
            factor["context"] = factor.pop("ctx")

    return data
