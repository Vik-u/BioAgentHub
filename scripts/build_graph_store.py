#!/usr/bin/env python3
"""Populate a lightweight SQLite graph store from kg_edges.jsonl."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, Tuple


def infer_node_type(label: str) -> str:
    """Best-effort node classification for quick filtering."""
    lower = label.lower()
    if lower.endswith("ase"):
        return "enzyme"
    if lower.startswith("ph"):
        return "condition"
    if lower.endswith("°c") or "°c" in lower or " c" in lower:
        return "condition"
    if "%" in label or "degrad" in lower or "conversion" in lower:
        return "metric"
    if lower in {"pet", "mhet", "bhet", "tpa"}:
        return "substrate"
    return "entity"


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            relation TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            paper TEXT,
            sentence TEXT,
            UNIQUE (source_id, relation, target_id, paper),
            FOREIGN KEY (source_id) REFERENCES nodes(id),
            FOREIGN KEY (target_id) REFERENCES nodes(id)
        );
        """
    )
    conn.commit()


def upsert_node(conn: sqlite3.Connection, cache: Dict[str, int], label: str) -> int:
    if label in cache:
        return cache[label]
    node_type = infer_node_type(label)
    cur = conn.execute(
        "INSERT OR IGNORE INTO nodes(label, type) VALUES(?, ?)",
        (label, node_type),
    )
    if cur.lastrowid is None:
        row = conn.execute("SELECT id FROM nodes WHERE label = ?", (label,)).fetchone()
        node_id = row[0]
    else:
        node_id = cur.lastrowid
    cache[label] = node_id
    return node_id


def iter_edges(path: Path) -> Iterable[Tuple[str, str, str, str, str]]:
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            yield (
                payload["source"],
                payload["relation"],
                payload["target"],
                payload.get("paper", ""),
                payload.get("sentence", ""),
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--edges",
        type=Path,
        default=Path("KnowledgeGraph/kg_edges.jsonl"),
        help="Path to the JSONL edge file.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("KnowledgeGraph/graph.sqlite"),
        help="Output SQLite database path.",
    )
    args = parser.parse_args()

    if not args.edges.exists():
        raise SystemExit(f"Edge file not found: {args.edges}")

    args.database.parent.mkdir(parents=True, exist_ok=True)
    if args.database.exists():
        args.database.unlink()

    conn = sqlite3.connect(args.database)
    ensure_schema(conn)

    cache: Dict[str, int] = {}
    inserted = 0
    for source, relation, target, paper, sentence in iter_edges(args.edges):
        src_id = upsert_node(conn, cache, source)
        tgt_id = upsert_node(conn, cache, target)
        conn.execute(
            """
            INSERT OR IGNORE INTO edges(source_id, relation, target_id, paper, sentence)
            VALUES(?, ?, ?, ?, ?)
            """,
            (src_id, relation, tgt_id, paper, sentence),
        )
        inserted += 1

    conn.commit()
    node_count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    edge_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    conn.close()
    print(f"Graph built with {node_count} nodes and {edge_count} edges (from {inserted} rows).")


if __name__ == "__main__":
    main()
