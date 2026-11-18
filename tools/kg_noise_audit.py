#!/usr/bin/env python3
"""Audit KG edge files for duplicates and unit-noise signals."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.ops_tracking import start_run, log_artifact, finalize_run  # noqa: E402

KG_PATTERNS = (
    "kg_edges.jsonl",
    "methodology_kg_edges.jsonl",
    "timeline_edges.jsonl",
)

NOISE_PATTERNS = {
    "unit_lower_m": re.compile(r"\b\d+(?:\.\d+)?\s*m\b"),
    "unit_lower_l": re.compile(r"\b\d+(?:\.\d+)?\s*l\b"),
    "unit_nm": re.compile(r"\b\d+(?:\.\d+)?\s*nm\b", re.IGNORECASE),
    "deg_missing_unit": re.compile(r"\b\d+(?:\.\d+)?\s*°(?!\s*[CFK])"),
    "linebreak": re.compile(r"\n|\r"),
    "hyphen_break": re.compile(r"-\s*\n"),
    "od600_as_conc": re.compile(r"\bOD\s*600\b", re.IGNORECASE),
    "wavelength_600nm": re.compile(r"\b600\s*nm\b", re.IGNORECASE),
}


def iter_kg_files(root: Path) -> List[Path]:
    paths = []
    for pattern in KG_PATTERNS:
        paths.extend(root.rglob(f"*{pattern}"))
    extra = root / "InstrumentGraph" / "kg_edges.jsonl"
    if extra.exists() and extra not in paths:
        paths.append(extra)
    # Deduplicate and sort
    return sorted({p.resolve() for p in paths})


def sample_json_line(path: Path) -> Dict:
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            return json.loads(line)
    return {}


def classify_edge(sample: Dict) -> str:
    keys = set(sample.keys())
    if {"instrument", "relation", "value"}.issubset(keys):
        return "instrument_kg"
    if {"source", "relation", "target"}.issubset(keys) and "sentence" not in keys and len(keys) <= 4:
        return "timeline_kg"
    if {"source", "relation", "target"}.issubset(keys):
        return "kg_edges"
    if {"paper", "relation", "value"}.issubset(keys):
        return "methodology_kg"
    return "unknown"


def subject_relation_object(edge: Dict, edge_type: str) -> Tuple[str, str, str]:
    relation = str(edge.get("relation", ""))
    if edge_type == "instrument_kg":
        return str(edge.get("instrument", "")), relation, str(edge.get("value", ""))
    if edge_type == "methodology_kg":
        return str(edge.get("paper", "")), relation, str(edge.get("value", ""))
    if edge_type == "kg_edges":
        return str(edge.get("source", "")), relation, str(edge.get("target", ""))
    if edge_type == "timeline_kg":
        return str(edge.get("source", "")), relation, str(edge.get("target", ""))
    return "", relation, ""


def relation_value(edge: Dict, edge_type: str) -> Tuple[str, str]:
    relation = str(edge.get("relation", ""))
    if edge_type in {"instrument_kg", "methodology_kg"}:
        return relation, str(edge.get("value", ""))
    return relation, str(edge.get("target", ""))


def detect_noise(edge: Dict, edge_type: str) -> bool:
    if edge_type == "timeline_kg":
        return False
    value = ""
    if edge_type in {"instrument_kg", "methodology_kg"}:
        value = str(edge.get("value", "") or "")
    else:
        value = str(edge.get("target", "") or "")
    sentence = str(edge.get("sentence", "") or "")
    text = f"{value} {sentence}".strip()
    if not text:
        return False
    for name, pattern in NOISE_PATTERNS.items():
        if pattern.search(text):
            if name in {"od600_as_conc", "wavelength_600nm"}:
                # Only flag if relation implies concentration-like value
                relation = str(edge.get("relation", "")).lower()
                if "concentration" in relation or "active" in relation or "temperature" in relation:
                    return True
                continue
            return True
    return False


def audit_file(path: Path) -> Dict:
    sample = sample_json_line(path)
    edge_type = classify_edge(sample) if sample else "unknown"
    total = 0
    exact_set = set()
    sro_set = set()
    rel_val_set = set()
    noise_count = 0
    noise_rel = Counter()
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                payload = json.loads(line)
            except Exception:
                continue
            exact_key = json.dumps(payload, sort_keys=True, ensure_ascii=False)
            exact_set.add(exact_key)
            sro_set.add(subject_relation_object(payload, edge_type))
            rel_val_set.add(relation_value(payload, edge_type))
            if detect_noise(payload, edge_type):
                noise_count += 1
                rel = str(payload.get("relation", ""))
                noise_rel[rel] += 1
    dup_exact = total - len(exact_set)
    dup_sro = total - len(sro_set)
    dup_rel_val = total - len(rel_val_set)
    top_noisy = [rel for rel, _ in noise_rel.most_common(10)]
    return {
        "name": path.name,
        "path": str(path),
        "edge_type": edge_type,
        "edge_count": total,
        "dup_exact": dup_exact,
        "dup_sro": dup_sro,
        "dup_rel_val": dup_rel_val,
        "unit_noise_count": noise_count,
        "top_noisy_relations": top_noisy,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repo root")
    parser.add_argument("--metrics-out", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    run_id, _ = start_run("kg_noise_audit", {"root": str(args.root)}, "KG noise audit")

    kg_files = iter_kg_files(args.root)
    results = [audit_file(path) for path in kg_files]
    payload = {"kgs": results}

    if args.metrics_out:
        args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
        args.metrics_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        log_artifact(run_id, str(args.metrics_out), "KG noise metrics JSON")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    finalize_run(run_id, ["KG noise audit completed"], None)


if __name__ == "__main__":
    main()
