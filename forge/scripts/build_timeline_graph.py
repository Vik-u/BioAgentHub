#!/usr/bin/env python3
"""
Build a simple timeline graph per workspace using PDF metadata (best-effort year extraction).

Outputs:
- timeline_edges.jsonl (precedes relations between papers sorted by year)
- timeline_overview.json (counts)
- timeline.sqlite (nodes: papers, edges: precedes)
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Dict, List


def load_metadata(meta_dir: Path) -> List[Dict[str, str]]:
    entries = []
    for path in sorted(meta_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        entries.append(data)
    return entries


def extract_year(entry: Dict[str, str]) -> int | None:
    # Try title_candidate, then pdf_file stem, then file name.
    candidates = [
        entry.get("title_candidate") or "",
        entry.get("pdf_file") or "",
        Path(entry.get("pdf_file", "")).stem,
    ]
    for text in candidates:
        m = re.search(r"(19|20)\d{2}", text)
        if m:
            try:
                return int(m.group(0))
            except ValueError:
                continue
    return None


def build_timeline(entries: List[Dict[str, str]]) -> List[Dict[str, str | int]]:
    annotated = []
    for e in entries:
        year = extract_year(e)
        annotated.append(
            {
                "pdf_file": e.get("pdf_file"),
                "title": e.get("title_candidate") or Path(e.get("pdf_file", "")).stem,
                "year": year,
            }
        )
    # Sort by year, fallback to name if unknown year.
    annotated.sort(key=lambda x: (x["year"] if x["year"] is not None else 9999, x["title"]))
    edges = []
    for idx in range(len(annotated) - 1):
        src = annotated[idx]
        tgt = annotated[idx + 1]
        if src["pdf_file"] and tgt["pdf_file"]:
            edges.append(
                {
                    "source": src["pdf_file"],
                    "target": tgt["pdf_file"],
                    "relation": "precedes",
                    "source_year": src["year"],
                    "target_year": tgt["year"],
                }
            )
    return edges


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS timeline_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT UNIQUE NOT NULL,
            year INTEGER
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS timeline_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            relation TEXT NOT NULL,
            source_year INTEGER,
            target_year INTEGER,
            UNIQUE(source_id, target_id, relation),
            FOREIGN KEY (source_id) REFERENCES timeline_nodes(id),
            FOREIGN KEY (target_id) REFERENCES timeline_nodes(id)
        );
        """
    )
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace root containing metadata/*.json")
    args = parser.parse_args()

    meta_dir = args.workspace / "metadata"
    if not meta_dir.exists():
        raise SystemExit(f"Metadata dir not found: {meta_dir}")

    entries = load_metadata(meta_dir)
    edges = build_timeline(entries)

    # Save JSONL and overview
    out_edges = args.workspace / "timeline_edges.jsonl"
    with out_edges.open("w", encoding="utf-8") as handle:
        for edge in edges:
            handle.write(json.dumps(edge, ensure_ascii=False) + "\n")

    with_year = sum(1 for e in entries if extract_year(e) is not None)
    overview = {
        "paper_count": len(entries),
        "edge_count": len(edges),
        "with_year": with_year,
    }
    (args.workspace / "timeline_overview.json").write_text(json.dumps(overview, indent=2))

    # Build SQLite
    db_path = args.workspace / "timeline.sqlite"
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    ensure_schema(conn)

    node_cache: Dict[str, int] = {}
    for e in entries:
        label = e.get("pdf_file") or e.get("title_candidate") or ""
        year = extract_year(e)
        cur = conn.execute(
            "INSERT OR IGNORE INTO timeline_nodes(label, year) VALUES(?, ?)",
            (label, year),
        )
        if cur.lastrowid is None:
            row = conn.execute("SELECT id FROM timeline_nodes WHERE label = ?", (label,)).fetchone()
            node_id = row[0]
        else:
            node_id = cur.lastrowid
        node_cache[label] = node_id

    inserted = 0
    for edge in edges:
        src_id = node_cache.get(edge["source"])
        tgt_id = node_cache.get(edge["target"])
        if src_id is None or tgt_id is None:
            continue
        conn.execute(
            """
            INSERT OR IGNORE INTO timeline_edges(source_id, target_id, relation, source_year, target_year)
            VALUES(?, ?, ?, ?, ?)
            """,
            (src_id, tgt_id, edge["relation"], edge["source_year"], edge["target_year"]),
        )
        inserted += 1
    conn.commit()
    conn.close()
    print(f"Timeline graph ready at {db_path} ({len(entries)} papers, {inserted} edges)")


if __name__ == "__main__":
    main()
