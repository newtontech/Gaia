# Local Storage

> **Status:** Current canonical

This document describes the embedded storage configuration used by the CLI for local development and `gaia publish --local`. For server-side storage architecture, see [../lkm/storage.md](../lkm/storage.md).

## Embedded Backends

The CLI uses embedded (in-process) storage backends:

| Backend | Implementation | Purpose |
|---------|---------------|---------|
| **LanceDB embedded** | `LanceContentStore` with local path | Content persistence, BM25 full-text search |
| **Kuzu embedded** | `KuzuGraphStore` | Graph topology for traversal queries |
| **LanceDB Vector** | `LanceVectorStore` (same LanceDB connection) | Embedding similarity search |

Both LanceDB and Kuzu run as embedded databases -- no separate server process is needed.

## Configuration

| Setting | Source | Default |
|---------|--------|---------|
| `GAIA_LANCEDB_PATH` | env var or `--db-path` | `./data/lancedb/gaia` |
| `graph_backend` | `StorageConfig` | `"kuzu"` (embedded) |

The LanceDB path controls where all content, vector, and Kuzu graph data is stored locally.

## `gaia publish --local` Triple-Write

When publishing locally, the CLI runs the full three-write protocol via `StorageManager`:

```
1. Write package with status="preparing"  (invisible to reads)
2. Write to ContentStore:  package, modules, knowledge, chains, factors
3. Write to GraphStore:    topology (knowledge -> chain relationships)
4. Write to VectorStore:   embeddings
5. Flip status to "merged"  (visible to reads)
```

On failure, data stays in "preparing" status -- invisible to readers and safe to retry.

## `gaia search` via BM25

`gaia search` queries the local LanceDB content store:

- **Primary**: BM25 full-text search via LanceDB's built-in FTS indexing.
- **Fallback**: SQL `LIKE` filter for CJK/unsegmented text.
- **Direct lookup**: `--id <knowledge_id>` fetches a specific knowledge item with latest belief from `belief_history`.

## Code Paths

| Component | File |
|-----------|------|
| Storage config | `libs/storage/config.py:StorageConfig` |
| Storage manager | `libs/storage/manager.py:StorageManager` |
| Content store | `libs/storage/lance_content_store.py:LanceContentStore` |
| Graph store (Kuzu) | `libs/storage/kuzu_graph_store.py:KuzuGraphStore` |
| Vector store | `libs/storage/lance_vector_store.py:LanceVectorStore` |
| CLI publish command | `cli/main.py` |
| Pipeline publish | `libs/pipeline.py:pipeline_publish()` |

## Current State

Local storage works with embedded LanceDB and Kuzu. The `publish --local` path exercises the full three-write protocol. BM25 search is functional. The graph backend is optional -- the system degrades gracefully to content-only mode.
