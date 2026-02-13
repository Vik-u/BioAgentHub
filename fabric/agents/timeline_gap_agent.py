#!/usr/bin/env python3
"""
Timeline- and KG-aware gap detector to support hypothesis generation.

Given a workspace, it looks at metadata years and timeline edges, then surfaces:
- Year span, missing years, earliest/latest paper.
- Basic KG coverage (edge count) if kg_edges.jsonl exists.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def load_jsonl(path: Path) -> List[Dict]:
    items: List[Dict] = []
    if not path.exists():
        return items
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def load_metadata(meta_dir: Path) -> List[Dict]:
    entries = []
    for path in sorted(meta_dir.glob("*.json")):
        try:
            entries.append(json.loads(path.read_text()))
        except Exception:
            continue
    return entries


def extract_year(entry: Dict) -> Optional[int]:
    for key in ("title_candidate", "pdf_file"):
        val = entry.get(key) or ""
        for token in val.replace("-", " ").split():
            if token.isdigit() and len(token) == 4:
                try:
                    year = int(token)
                except ValueError:
                    continue
                if 1900 <= year <= 2100:
                    return year
    return None


def summarize_timeline(entries: List[Dict]) -> Dict:
    with_year = []
    for e in entries:
        yr = extract_year(e)
        if yr is not None:
            with_year.append((yr, e.get("pdf_file") or e.get("title_candidate") or ""))
    if not with_year:
        return {"paper_count": len(entries), "with_year": 0, "note": "No year metadata found."}

    years = [y for y, _ in with_year]
    year_counts = Counter(years)
    earliest = min(with_year, key=lambda x: x[0])
    latest = max(with_year, key=lambda x: x[0])
    span = (earliest[0], latest[0])
    gaps = [y for y in range(span[0], span[1] + 1) if y not in year_counts]

    return {
        "paper_count": len(entries),
        "with_year": len(with_year),
        "year_span": span,
        "top_years": year_counts.most_common(5),
        "earliest": {"year": earliest[0], "paper": earliest[1]},
        "latest": {"year": latest[0], "paper": latest[1]},
        "missing_years": gaps[:50],
    }


def summarize_kg_edges(edge_path: Path) -> Dict:
    edges = load_jsonl(edge_path)
    rel_counts = Counter(e.get("relation") for e in edges)
    sources = Counter(e.get("source") for e in edges)
    return {
        "edge_count": len(edges),
        "top_relations": rel_counts.most_common(5),
        "top_sources": sources.most_common(5),
    }


def summarize_workspace(workspace: Path) -> Dict:
    meta_dir = workspace / "metadata"
    edges_path = workspace / "kg_edges.jsonl"
    timeline_edges = workspace / "timeline_edges.jsonl"
    metadata = load_metadata(meta_dir) if meta_dir.exists() else []
    timeline_summary = summarize_timeline(metadata)
    kg_summary = summarize_kg_edges(edges_path) if edges_path.exists() else {"note": "kg_edges.jsonl not found"}
    timeline_edges_note = "present" if timeline_edges.exists() else "missing"
    return {
        "workspace": str(workspace),
        "timeline": timeline_summary,
        "timeline_edges": timeline_edges_note,
        "kg": kg_summary,
    }


if __name__ == "__main__":
    import argparse
    import json as pyjson

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    print(pyjson.dumps(summarize_workspace(args.workspace), indent=2))
