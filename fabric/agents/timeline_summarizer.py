#!/usr/bin/env python3
"""
Summarize the evolution of a topic using the timeline graph for a workspace.

Usage:
  python agents/timeline_summarizer.py --workspace workspaces/petase
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple


def load_metadata(meta_dir: Path) -> List[Dict]:
    entries = []
    for path in sorted(meta_dir.glob("*.json")):
        try:
            entries.append(json.loads(path.read_text()))
        except Exception:
            continue
    return entries


def extract_year(entry: Dict) -> int | None:
    for key in ("title_candidate", "pdf_file"):
        val = entry.get(key) or ""
        for token in val.split():
            if token.isdigit() and len(token) == 4:
                try:
                    year = int(token)
                except ValueError:
                    continue
                if 1900 <= year <= 2100:
                    return year
    return None


def summarize_timeline(entries: List[Dict]) -> Dict:
    with_year = [(extract_year(e), e.get("pdf_file") or e.get("title_candidate") or "") for e in entries]
    with_year = [(y, name) for y, name in with_year if y is not None]
    if not with_year:
        return {"paper_count": len(entries), "with_year": 0, "summary": "No year metadata found."}

    years = [y for y, _ in with_year]
    year_counts = Counter(years)
    earliest = min(with_year, key=lambda x: x[0])
    latest = max(with_year, key=lambda x: x[0])
    span = (earliest[0], latest[0])
    gaps = []
    for y in range(span[0], span[1]):
        if y not in year_counts:
            gaps.append(y)

    return {
        "paper_count": len(entries),
        "with_year": len(with_year),
        "year_span": span,
        "top_years": year_counts.most_common(5),
        "earliest": earliest,
        "latest": latest,
        "missing_years": gaps[:20],  # cap for brevity
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace root containing metadata/")
    args = parser.parse_args()

    meta_dir = args.workspace / "metadata"
    if not meta_dir.exists():
        raise SystemExit(f"Metadata directory not found: {meta_dir}")

    entries = load_metadata(meta_dir)
    summary = summarize_timeline(entries)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
