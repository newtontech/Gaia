# LKM Overview

> **Status:** Current canonical

The Large Knowledge Model (LKM) is a computational registry -- not just storage, but an active system that validates, canonicalizes, reviews, integrates, curates, and infers over the global knowledge graph. **The LKM never sees Gaia Lang -- it operates entirely on Graph IR.**

## Architecture

The LKM has two sides:

### Write Side (Package Lifecycle)

When a package is published, it enters the server-side lifecycle:

```
validate  ->  canonicalize  ->  review  ->  [rebuttal]  ->  integrate  ->  curate  ->  global BP
```

Each stage is detailed in its own document:
- [review-pipeline.md](review-pipeline.md) -- peer review and probability assignment
- [global-canonicalization.md](global-canonicalization.md) -- local-to-global node mapping
- [curation.md](curation.md) -- offline graph maintenance
- [global-inference.md](global-inference.md) -- server-side belief propagation
- [pipeline.md](pipeline.md) -- batch orchestration
- [lifecycle.md](lifecycle.md) -- full stage-by-stage breakdown

### Read Side (Query Service)

The LKM exposes published knowledge via HTTP API endpoints:

- Package and module browsing
- Knowledge item retrieval with version history
- Chain and probability history
- Graph topology for DAG visualization
- BM25 full-text search (planned: vector similarity search)

See [api.md](api.md) for endpoint details.

## Implementation

The LKM is implemented as a FastAPI gateway (`services/gateway/`):

- **Application factory**: `services/gateway/app.py` exports `create_app(dependencies=None)`.
- **Dependency injection**: `services/gateway/deps.py` holds a `Dependencies` class with a `StorageManager` singleton. Tests inject custom dependencies via `create_app(dependencies=...)`.
- **Startup**: loads `.env`, initializes `StorageManager` from `StorageConfig`, connects content/graph/vector stores.
- **CORS**: allows `localhost:5173` for the frontend dev server.

Run with:

```bash
GAIA_LANCEDB_PATH=./data/lancedb/gaia \
  uvicorn services.gateway.app:create_app --factory --reload --host 0.0.0.0 --port 8000
```

## Layered Architecture

```
Entry Points
  Server  (services/gateway/)    -- FastAPI HTTP API
  Pipeline scripts  (scripts/)   -- batch orchestration

         | call

Engines
  Canonicalization  (libs/global_graph/) -- local -> global node mapping
  Review Pipeline  (services/review_pipeline/) -- review scoring
  Curation  (services/curation/)         -- offline graph maintenance
  BP Engine  (libs/inference/)           -- sum-product loopy BP

         | use

Storage
  LanceDB  (libs/storage/lance_content_store.py)  -- content + FTS + metadata
  Neo4j/Kuzu  (libs/storage/)  -- graph topology
  LanceDB Vector  (libs/storage/lance_vector_store.py)  -- embedding similarity
```

Dependencies flow strictly downward. `libs/` has no service dependencies. The CLI and server are independent product surfaces sharing the same `libs/` layer.

## End-to-End Data Flow (Server Side)

```
5. Global Canonicalization
   libs/global_graph/canonicalize.py  ->  map local nodes to global nodes
       |  produces CanonicalBindings + GlobalCanonicalNodes + global factors
6. Persist (StorageManager three-write)
   libs/storage/manager.py  ->  content -> graph -> vector
       |
7. Curation (offline)
   services/curation/  ->  similarity clustering, contradiction discovery
       |
8. Global BP (server)
   Same libs/inference/ engine on the global canonical graph
```

Steps 1-4 (authoring, build, local BP) happen locally via the CLI. See [../cli/lifecycle.md](../cli/lifecycle.md).

## Key Design Decisions

- **Graph IR as the interface boundary.** The LKM receives Graph IR (raw graphs, local canonical graphs) -- never Typst source. This decouples the authoring DSL from the registry.
- **Structure vs. parameters separated.** Graph IR stores structural relationships. Priors, beliefs, and factor params live in `GlobalInferenceState`. See [../graph-ir/parameterization.md](../graph-ir/parameterization.md).
- **Three-write atomicity.** Package ingestion writes content (source of truth), graph (topology), and vector (embeddings) with visibility gating. See [storage.md](storage.md).
- **Graceful degradation.** Graph and vector stores are optional. The system operates with content store alone.

## Code Paths

| Component | File |
|-----------|------|
| App factory | `services/gateway/app.py` |
| Dependencies | `services/gateway/deps.py` |
| Routes | `services/gateway/routes/packages.py` |
| Storage manager | `libs/storage/manager.py` |
| Storage config | `libs/storage/config.py` |
| Global canonicalization | `libs/global_graph/canonicalize.py` |
| BP engine | `libs/inference/bp.py` |

## Current State

The server is a read-heavy API with a single bulk-write endpoint (`/packages/ingest`). The frontend at `localhost:5173` consumes these endpoints for DAG visualization and knowledge browsing. Server-side review, curation, and global BP are available via pipeline scripts but not yet as HTTP-triggered services.

## Target State

- **Write side**: Add server-side `ReviewService` (LLM review on ingest) and `CurationService` (background graph maintenance).
- **Read side**: Separate read routes into distinct routers for independent scaling.
- Wire `gaia publish --server` to `POST /packages/ingest`.
