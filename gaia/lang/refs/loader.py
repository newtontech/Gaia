"""Load and validate references.json (CSL-JSON format).

Per spec §4, stores entries as a dict keyed by citation key (not the
standard CSL-JSON array form). Missing file is not an error — references.json
is optional.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gaia.lang.refs.errors import ReferenceError

# CSL 1.0.2 type allowlist.
# Source: https://github.com/citation-style-language/schema
_CSL_TYPES: frozenset[str] = frozenset(
    {
        "article",
        "article-journal",
        "article-magazine",
        "article-newspaper",
        "bill",
        "book",
        "broadcast",
        "chapter",
        "classic",
        "collection",
        "dataset",
        "document",
        "entry",
        "entry-dictionary",
        "entry-encyclopedia",
        "event",
        "figure",
        "graphic",
        "hearing",
        "interview",
        "legal_case",
        "legislation",
        "manuscript",
        "map",
        "motion_picture",
        "musical_score",
        "pamphlet",
        "paper-conference",
        "patent",
        "performance",
        "periodical",
        "personal_communication",
        "post",
        "post-weblog",
        "regulation",
        "report",
        "review",
        "review-book",
        "software",
        "song",
        "speech",
        "standard",
        "thesis",
        "treaty",
        "webpage",
    }
)


def load_references(path: Path) -> dict[str, dict[str, Any]]:
    """Load and validate a references.json file.

    Args:
        path: Path to references.json. If missing, returns an empty dict.

    Returns:
        dict mapping citation key → CSL-JSON entry.

    Raises:
        ReferenceError: on invalid JSON, wrong top-level type, or any entry
            that fails schema validation.
    """
    if not path.exists():
        return {}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ReferenceError(
            f"invalid JSON in references file: {e.msg} (line {e.lineno}, col {e.colno})",
            location=str(path),
        ) from e

    if not isinstance(raw, dict):
        raise ReferenceError(
            f"references.json must be a JSON object keyed by citation key, "
            f"got {type(raw).__name__}",
            location=str(path),
        )

    for key, entry in raw.items():
        _validate_entry(key, entry, location=str(path))

    return raw


def _validate_entry(key: str, entry: Any, *, location: str) -> None:
    """Validate a single CSL-JSON entry.

    Minimum requirements (spec §4.5):
      - must be a dict
      - must have `type` matching CSL 1.0.2 allowlist
      - must have `title`
    """
    if not isinstance(entry, dict):
        raise ReferenceError(
            f"reference entry '{key}' must be an object, got {type(entry).__name__}",
            location=location,
        )

    if "type" not in entry:
        raise ReferenceError(
            f"reference entry '{key}' is missing required field 'type'",
            location=location,
        )
    entry_type = entry["type"]
    if entry_type not in _CSL_TYPES:
        raise ReferenceError(
            f"reference entry '{key}' has invalid type '{entry_type}'. "
            f"must be one of the CSL 1.0.2 types (e.g. article-journal, "
            f"book, webpage, software, dataset).",
            location=location,
        )

    if "title" not in entry or not entry["title"]:
        raise ReferenceError(
            f"reference entry '{key}' is missing required field 'title'",
            location=location,
        )
