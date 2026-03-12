#!/usr/bin/env python3
"""Query remote LanceDB on TOS for stats and exploration.

Usage:
    # Paper pipeline status
    python scripts/query_remote_lancedb.py papers

    # Knowledge graph stats
    python scripts/query_remote_lancedb.py graph

    # List all tables in a target
    python scripts/query_remote_lancedb.py papers --tables
    python scripts/query_remote_lancedb.py graph --tables

Reads TOS credentials from .env (TOS_ACCESS_KEY, TOS_SECRET_KEY, TOS_ENDPOINT).
"""

from __future__ import annotations

import argparse
import os
import sys
import warnings
from pathlib import Path

import lancedb
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Known remote databases
TARGETS = {
    "papers": {"bucket": "datainfra-prod", "path": "paper_data"},
    "graph": {"bucket": "datainfra-prod", "path": "propositional_logic_analysis"},
}


def connect(bucket: str, base_path: str) -> lancedb.DBConnection:
    ak = os.getenv("TOS_ACCESS_KEY")
    sk = os.getenv("TOS_SECRET_KEY")
    endpoint = os.getenv("TOS_ENDPOINT")
    if not all([ak, sk, endpoint]):
        print("ERROR: TOS_ACCESS_KEY, TOS_SECRET_KEY, TOS_ENDPOINT must be set in .env")
        sys.exit(1)
    uri = f"s3://{bucket}/{base_path}"
    opts = {
        "access_key_id": ak,
        "secret_access_key": sk,
        "endpoint": f"https://{bucket}.{endpoint}",
        "virtual_hosted_style_request": "true",
    }
    return lancedb.connect(uri, storage_options=opts)


def list_tables(db: lancedb.DBConnection) -> None:
    tables = sorted(db.table_names())
    print(f"Tables ({len(tables)}):")
    for name in tables:
        tbl = db.open_table(name)
        rows = tbl.count_rows()
        print(f"  {name}: {rows:,} rows")
        print(f"    schema: {tbl.schema}")
        print(f"    indexes: {tbl.list_indices()}")
        print()


def paper_stats(db: lancedb.DBConnection) -> None:
    tbl = db.open_table("metadata")
    total = tbl.count_rows()

    ocr_done = tbl.count_rows("ocr != 'none'")
    conc_extracted = tbl.count_rows("is_extract_conclusion = true")
    prem_extracted = tbl.count_rows("is_extract_premise = true")
    prob_extracted = tbl.count_rows("is_extract_problem = true")
    has_conclusions = tbl.count_rows("conclusion_num > 0")

    print(f"{'=' * 50}")
    print("  Paper Pipeline Status")
    print(f"{'=' * 50}")
    print(f"  Total papers:            {total:>12,}")
    print()
    print(f"  OCR completed:           {ocr_done:>12,}  ({ocr_done / total * 100:.1f}%)")
    print(
        f"  OCR pending:             {total - ocr_done:>12,}  ({(total - ocr_done) / total * 100:.1f}%)"
    )
    print()
    print(
        f"  Conclusion extracted:    {conc_extracted:>12,}  ({conc_extracted / total * 100:.1f}%)"
    )
    print(
        f"  Problem extracted:       {prob_extracted:>12,}  ({prob_extracted / total * 100:.1f}%)"
    )
    print(
        f"  Premise extracted:       {prem_extracted:>12,}  ({prem_extracted / total * 100:.1f}%)"
    )
    print(
        f"  Has conclusions (num>0): {has_conclusions:>12,}  ({has_conclusions / total * 100:.1f}%)"
    )
    print()


def graph_stats(db: lancedb.DBConnection) -> None:
    print(f"{'=' * 50}")
    print("  Knowledge Graph Stats")
    print(f"{'=' * 50}")

    for name in sorted(db.table_names()):
        tbl = db.open_table(name)
        rows = tbl.count_rows()
        print(f"  {name:20s}: {rows:>12,} rows")

    print()

    # Metadata rounds
    meta_tbl = db.open_table("metadata")
    sample = meta_tbl.head(100).to_pylist()
    print("  Round history:")
    for m in sorted(sample, key=lambda x: x["round"]):
        print(
            f"    round {m['round']:2d}: {m['change_type']:18s} "
            f"nodes={m['total_nodes']:>10,}  edges={m['total_edges']:>10,}  "
            f"active_nodes={m['active_nodes']:>10,}"
        )
    print()


def main():
    parser = argparse.ArgumentParser(description="Query remote LanceDB on TOS")
    parser.add_argument("target", choices=TARGETS.keys(), help="Which database to query")
    parser.add_argument("--tables", action="store_true", help="List all tables with schema")
    parser.add_argument(
        "--env",
        type=Path,
        default=Path(__file__).resolve().parent.parent / ".env",
        help="Path to .env file",
    )
    args = parser.parse_args()

    load_dotenv(args.env)
    target = TARGETS[args.target]
    db = connect(target["bucket"], target["path"])

    if args.tables:
        list_tables(db)
    elif args.target == "papers":
        paper_stats(db)
    elif args.target == "graph":
        graph_stats(db)


if __name__ == "__main__":
    main()
