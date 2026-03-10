"""Storage v2 configuration."""

import os
from typing import Literal

from pydantic import BaseModel


class StorageConfig(BaseModel):
    """Environment-driven storage configuration."""

    lancedb_path: str = os.environ.get("GAIA_LANCEDB_PATH", "/data/lancedb/gaia_v2")
    graph_backend: Literal["neo4j", "kuzu", "none"] = os.environ.get("GAIA_GRAPH_BACKEND", "kuzu")
    neo4j_uri: str = os.environ.get("GAIA_NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.environ.get("GAIA_NEO4J_USER", "neo4j")
    neo4j_password: str = os.environ.get("GAIA_NEO4J_PASSWORD", "")
    neo4j_database: str = os.environ.get("GAIA_NEO4J_DATABASE", "neo4j")
    kuzu_path: str | None = None
    vector_index_type: Literal["diskann", "ivf_pq"] = "diskann"
