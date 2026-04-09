"""Backfill package_id and role for existing embeddings in ByteHouse.

Reads from LanceDB:
- global_variable_nodes.representative_lcn → package_id
- global_factor_nodes.premises/conclusion → role (conclusion > premise)

Then re-inserts into ByteHouse node_embeddings_v2 (HaUniqueMergeTree deduplicates).

Usage: python scripts/backfill_embedding_metadata.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, f"backfill-{time.strftime('%Y%m%d-%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(_LOG_FILE)],
    force=True,
)
logger = logging.getLogger(__name__)
logger.info("Log file: %s", _LOG_FILE)


async def main():
    from gaia.lkm.storage.bytehouse_store import ByteHouseEmbeddingStore
    from gaia.lkm.storage.config import StorageConfig
    from gaia.lkm.storage.lance_store import LanceContentStore

    t0 = time.time()
    cfg = StorageConfig()
    logger.info("Starting backfill. LanceDB URI: %s", cfg.effective_lancedb_uri)

    # Init LanceDB
    logger.info("Connecting to LanceDB...")
    lance = LanceContentStore(cfg.effective_lancedb_uri, storage_options=cfg.storage_options)
    await lance.initialize()
    logger.info("[%.0fs] LanceDB ready", time.time() - t0)

    # Init ByteHouse
    bh = ByteHouseEmbeddingStore(
        host=cfg.bytehouse_host,
        user=cfg.bytehouse_user,
        password=cfg.bytehouse_password,
        database=cfg.bytehouse_database,
        replication_root=cfg.bytehouse_replication_root,
    )
    logger.info("[%.0fs] ByteHouse ready", time.time() - t0)

    # Step 1: Get all embedded gcn_ids that need backfill
    needs_backfill = bh._client.query(
        f"SELECT gcn_id FROM {bh.TABLE} WHERE package_id = '' OR role = ''"
    )
    gcn_ids = [r[0] for r in needs_backfill.result_rows]
    logger.info("[%.0fs] Need backfill: %d gcn_ids", time.time() - t0, len(gcn_ids))

    if not gcn_ids:
        logger.info("Nothing to backfill")
        bh.close()
        return

    # Step 2: Load gcn_id → package_id from LanceDB global_variable_nodes
    logger.info("[%.0fs] Loading global variable nodes from LanceDB...", time.time() - t0)
    db = lance._db
    gvar_table = db.open_table("global_variable_nodes")
    total_gvars = await lance._run(gvar_table.count_rows)
    all_gvars = await lance._run(
        lambda: gvar_table.search()
        .select(["id", "representative_lcn"])
        .limit(max(total_gvars, 100000))
        .to_list()
    )

    gcn_to_package: dict[str, str] = {}
    for g in all_gvars:
        try:
            rep = json.loads(g["representative_lcn"])
            gcn_to_package[g["id"]] = rep.get("package_id", "")
        except (KeyError, json.JSONDecodeError):
            pass
    logger.info(
        "[%.0fs] Loaded %d gcn→package mappings", time.time() - t0, len(gcn_to_package)
    )

    # Step 3: Load gcn_id → role from LanceDB global_factor_nodes
    logger.info("[%.0fs] Loading global factor nodes for role mapping...", time.time() - t0)
    gfac_table = db.open_table("global_factor_nodes")
    total_gfacs = await lance._run(gfac_table.count_rows)
    all_gfacs = await lance._run(
        lambda: gfac_table.search()
        .select(["premises", "conclusion"])
        .limit(max(total_gfacs, 100000))
        .to_list()
    )

    conclusions: set[str] = set()
    premises: set[str] = set()
    for f in all_gfacs:
        try:
            conclusion = f["conclusion"]
            if conclusion:
                conclusions.add(conclusion)
            for p in json.loads(f["premises"]):
                premises.add(p)
        except (KeyError, json.JSONDecodeError, TypeError):
            pass

    def get_role(gcn_id: str) -> str:
        # conclusion takes priority (if both, mark as conclusion)
        if gcn_id in conclusions:
            return "conclusion"
        if gcn_id in premises:
            return "premise"
        return ""

    logger.info(
        "[%.0fs] Role mapping: %d conclusions, %d premises",
        time.time() - t0,
        len(conclusions),
        len(premises),
    )

    # Step 4: Re-insert into ByteHouse with package_id and role
    # Read existing embeddings in batches and re-insert with metadata
    batch_size = 5000
    updated = 0

    for i in range(0, len(gcn_ids), batch_size):
        batch_ids = gcn_ids[i : i + batch_size]
        in_clause = ", ".join(f"'{gid}'" for gid in batch_ids)

        rows = bh._client.query(
            f"SELECT gcn_id, content, node_type, embedding, source_id "
            f"FROM {bh.TABLE} WHERE gcn_id IN ({in_clause})"
        )

        records = []
        for r in rows.result_rows:
            gcn_id = r[0]
            records.append([
                gcn_id,
                gcn_to_package.get(gcn_id, ""),
                r[1],  # content
                r[2],  # node_type
                get_role(gcn_id),
                r[3],  # embedding
                r[4],  # source_id
            ])

        if records:
            bh._client.insert(
                bh.TABLE,
                records,
                column_names=bh._COLUMNS,
            )
            updated += len(records)

        logger.info(
            "[%.0fs] Backfilled %d/%d (batch %d)",
            time.time() - t0,
            updated,
            len(gcn_ids),
            i // batch_size + 1,
        )

    # Step 5: Verify
    verify = bh._client.query(f"""
        SELECT
            countIf(package_id != '') as has_pkg,
            countIf(package_id = '') as no_pkg,
            countIf(role = 'conclusion') as conclusions,
            countIf(role = 'premise') as premises,
            countIf(role = '') as no_role,
            count() as total
        FROM {bh.TABLE}
    """)
    v = verify.result_rows[0]
    logger.info(
        "[%.0fs] Done. total=%d, has_pkg=%d, no_pkg=%d, conclusions=%d, premises=%d, no_role=%d",
        time.time() - t0, v[5], v[0], v[1], v[2], v[3], v[4],
    )

    # Step 6: Refresh embedding status
    status = bh.refresh_embedding_status()
    logger.info("[%.0fs] Embedding status refreshed: %s", time.time() - t0, status)

    bh.close()


if __name__ == "__main__":
    asyncio.run(main())
