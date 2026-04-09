"""Pipeline: compute embeddings for all pending public global variables.

Incremental: skips gcn_ids already in ByteHouse.
After completion, refreshes embedding_status table.

Usage:
    python -m gaia.lkm.pipelines.embedding
    python -m gaia.lkm.pipelines.embedding --dry-run
"""

from __future__ import annotations

import asyncio
import logging

from gaia.lkm.models.discovery import DiscoveryConfig

logger = logging.getLogger(__name__)


def _create_bytehouse(config=None):
    """Create ByteHouseEmbeddingStore from env config."""
    from gaia.lkm.storage.bytehouse_store import ByteHouseEmbeddingStore
    from gaia.lkm.storage.config import StorageConfig

    cfg = config or StorageConfig()
    if not cfg.bytehouse_host:
        raise RuntimeError("ByteHouse not configured — set BYTEHOUSE_HOST env var")
    return ByteHouseEmbeddingStore(
        host=cfg.bytehouse_host,
        user=cfg.bytehouse_user,
        password=cfg.bytehouse_password,
        database=cfg.bytehouse_database,
        replication_root=cfg.bytehouse_replication_root,
    ), cfg


async def run_embedding_pipeline(
    config: DiscoveryConfig | None = None,
) -> dict:
    """Compute embeddings for all pending public global variables.

    1. Init LanceDB (skip Neo4j) + ByteHouse
    2. Compute embeddings incrementally
    3. Refresh embedding_status table

    Returns stats dict: {total, computed, skipped, failed}.
    """
    from gaia.lkm.core._embedding import compute_embeddings
    from gaia.lkm.storage.config import StorageConfig
    from gaia.lkm.storage.lance_store import LanceContentStore

    if config is None:
        config = DiscoveryConfig()

    cfg = StorageConfig()

    # Init LanceDB only (skip Neo4j — embedding doesn't need graph)
    lance = LanceContentStore(cfg.effective_lancedb_uri, storage_options=cfg.storage_options)
    await lance.initialize()
    logger.info("LanceDB ready")

    bytehouse, _ = _create_bytehouse(cfg)
    bytehouse.ensure_all_tables()
    logger.info("ByteHouse ready")

    # Minimal storage wrapper (compute_embeddings needs list_all_public_global_ids
    # and get_local_variables_by_ids)
    class _LanceOnlyStorage:
        def __init__(self, content):
            self._content = content

        async def list_all_public_global_ids(self):
            return await self._content.list_all_public_global_ids()

        async def get_local_variables_by_ids(self, local_ids, concurrency=4):
            return await self._content.get_local_variables_by_ids(local_ids, concurrency)

    storage = _LanceOnlyStorage(lance)

    try:
        stats = await compute_embeddings(
            storage, bytehouse, config, access_key=cfg.embedding_access_key
        )
        logger.info("Embedding complete: %s", stats)

        # Refresh per-package status
        loop = asyncio.get_running_loop()
        status = await loop.run_in_executor(None, bytehouse.refresh_embedding_status)
        logger.info("Embedding status refreshed: %s", status)

        return stats
    finally:
        bytehouse.close()


async def dry_run() -> dict:
    """Report embedding status without computing anything."""
    from gaia.lkm.storage.config import StorageConfig
    from gaia.lkm.storage.lance_store import LanceContentStore

    cfg = StorageConfig()
    lance = LanceContentStore(cfg.effective_lancedb_uri, storage_options=cfg.storage_options)
    await lance.initialize()

    bytehouse, _ = _create_bytehouse(cfg)
    bytehouse.ensure_table()

    try:
        ids = await lance.list_all_public_global_ids()
        loop = asyncio.get_running_loop()
        existing = await loop.run_in_executor(None, bytehouse.get_existing_gcn_ids)

        summary = bytehouse.get_embedding_status_summary()

        return {
            "public_globals": len(ids),
            "already_embedded": len(existing),
            "pending": len(ids) - len(existing),
            "packages_tracked": summary.get("total_packages", 0),
        }
    finally:
        bytehouse.close()


if __name__ == "__main__":
    import argparse
    import json
    import os
    import time

    _LOG_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs"
    )
    os.makedirs(_LOG_DIR, exist_ok=True)
    _LOG_FILE = os.path.join(_LOG_DIR, f"embedding-{time.strftime('%Y%m%d-%H%M%S')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(_LOG_FILE),
        ],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(description="Compute embeddings for pending variables")
    parser.add_argument("--dry-run", action="store_true", help="Report status without computing")
    args = parser.parse_args()

    async def main():
        if args.dry_run:
            stats = await dry_run()
            print(json.dumps(stats, indent=2))
        else:
            stats = await run_embedding_pipeline()
            print(json.dumps(stats, indent=2))

    asyncio.run(main())
