# Server Storage

> **Status:** Current canonical

This document describes the server-side storage architecture. For local (embedded) storage used by the CLI, see [../cli/local-storage.md](../cli/local-storage.md).

## Three-Backend Architecture

The storage layer uses three complementary backends, all managed by `StorageManager` (`libs/storage/manager.py`):

| Backend | Class | Purpose | Required? |
|---------|-------|---------|-----------|
| **LanceDB Content** | `LanceContentStore` | All entity persistence, BM25 full-text search | Yes (source of truth) |
| **Neo4j / Kuzu Graph** | `Neo4jGraphStore` / `KuzuGraphStore` | Graph topology for traversal queries | Optional |
| **LanceDB Vector** | `LanceVectorStore` | Embedding similarity search | Optional |

The content store is always required and serves as the source of truth. Graph and vector stores are optional -- the system degrades gracefully without them.

### Backend Selection

Configured via `StorageConfig` (`libs/storage/config.py`):

- **LanceDB**: Local path or remote S3/TOS URI. Remote mode uses `storage_options` with TOS access keys.
- **Graph backend**: `"kuzu"` (embedded, local default), `"neo4j"` (server), or `"none"`.
- **Vector store**: Always created alongside the content store (same LanceDB connection, separate table).

## StorageManager

`StorageManager` is the unified facade. Domain services interact only with this class, never with individual stores directly.

Key responsibilities:

- **Initialization**: instantiates and connects all configured stores.
- **Three-write atomicity**: coordinates multi-store writes with visibility gating.
- **Read delegation**: passes reads through to the appropriate store, with visibility filtering for graph queries.
- **Graceful degradation**: returns empty results when optional stores are unavailable.

## Three-Write Atomicity

See `libs/storage/manager.py:StorageManager.ingest_package()`.

Package ingestion follows a five-step protocol:

```
1. Write package with status="preparing"  (invisible to reads)
2. Write to ContentStore:  package, modules, knowledge, chains, factors, submission_artifact
3. Write to GraphStore:    topology (knowledge -> chain relationships), factor topology
4. Write to VectorStore:   embeddings
5. Flip status to "merged"  (visible to reads)
```

On failure, data stays in "preparing" status -- invisible to readers and safe to retry. The content store is always written first as the source of truth.

## LanceDB Table Schemas

All tables are defined as PyArrow schemas in `libs/storage/lance_content_store.py`:

### Core Entity Tables

| Table | Key | Purpose |
|-------|-----|---------|
| `packages` | `(package_id, version)` | Package metadata, status, modules list |
| `modules` | `module_id` | Module metadata, chain_ids, export_ids |
| `knowledge` | `(knowledge_id, version)` | Versioned propositions with type, content, prior, keywords |
| `chains` | `chain_id` | Reasoning chains with typed steps (premises -> conclusion) |

### Inference Tables

| Table | Key | Purpose |
|-------|-----|---------|
| `probabilities` | `(chain_id, step_index)` | Step reliability scores from various sources |
| `belief_history` | `(knowledge_id, version, bp_run_id)` | BP result snapshots over time |

### Graph IR Tables

| Table | Key | Purpose |
|-------|-----|---------|
| `factors` | `factor_id` | Persistent factors from Graph IR compilation |
| `canonical_bindings` | `(package, version, local_canonical_id)` | Local-to-global node mappings |
| `global_canonical_nodes` | `global_canonical_id` | Deduplicated cross-package knowledge identities |
| `global_inference_state` | singleton `_id` | Registry-managed global BP state (priors, beliefs, factor params) |

### Resource Tables

| Table | Key | Purpose |
|-------|-----|---------|
| `resources` | `resource_id` | Resource metadata (images, code, datasets) |
| `resource_attachments` | `(resource_id, target_id)` | Many-to-many links to knowledge/chains/modules |
| `submission_artifacts` | `(package_name, commit_hash)` | Immutable snapshots for audit |

## Graph Store Topology

The graph store (Neo4j or Kuzu) maintains topology for traversal queries:

- Knowledge nodes keyed by composite `knowledge_id@version`
- `:PREMISE` and `:CONCLUSION` relationships from chains
- Factor topology links
- Global canonical node topology and bindings

The graph store is always secondary to the content store. It is populated during the three-write protocol and can be rebuilt from content store data.

## Server vs Local Storage

| Aspect | Server | Local (CLI) |
|--------|--------|-------------|
| **LanceDB** | Remote S3/TOS URI or local path | Local path (`GAIA_LANCEDB_PATH`) |
| **Graph backend** | Neo4j (production) or Kuzu | Kuzu (embedded) |
| **Vector store** | Active | Active |
| **Access** | Via FastAPI gateway | Direct via `StorageManager` |
| **Concurrency** | Multi-reader, single writer | Single-user |

## Code Paths

| Component | File |
|-----------|------|
| Storage manager | `libs/storage/manager.py:StorageManager` |
| Storage config | `libs/storage/config.py:StorageConfig` |
| Content store | `libs/storage/lance_content_store.py:LanceContentStore` |
| Graph store (Neo4j) | `libs/storage/neo4j_graph_store.py:Neo4jGraphStore` |
| Graph store (Kuzu) | `libs/storage/kuzu_graph_store.py:KuzuGraphStore` |
| Vector store | `libs/storage/lance_vector_store.py:LanceVectorStore` |
| Data models | `libs/storage/models.py` |

## Current State

The storage layer is working in production with remote LanceDB (S3/TOS) and Neo4j. Local development uses embedded LanceDB and optionally Kuzu. BM25 full-text search is available via LanceDB's built-in FTS indexing. The three-write protocol is exercised by both the CLI publish path and the server ingestion pipeline.

## Target State

The storage layer is stable. No major schema changes are planned. The `global_inference_state` table was recently added and may see minor field additions as the inference pipeline matures.
