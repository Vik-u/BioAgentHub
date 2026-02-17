#!/usr/bin/env python3
"""Generate a deterministic top-candidates report from an existing vector store."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.output_paths import qa_dir  # noqa: E402

QA_OUTPUT_ROOT = qa_dir()

MUTATION_RE = re.compile(r"\b[A-Z]\d{1,4}[A-Z]\b")
COMBO_MUTATION_RE = re.compile(r"\b[A-Z]\d+[A-Z](?:/[A-Z]\d+[A-Z])+\b")
PETASE_RE = re.compile(r"\b[A-Za-z0-9-]*PETase[A-Za-z0-9-]*\b", re.IGNORECASE)
IS_PETASE_RE = re.compile(r"\bIs\\s+PETase\b", re.IGNORECASE)

POSITIVE_KWS = (
    "improve", "improved", "increase", "increased", "enhanced", "higher", "better",
    "greater", "more active", "more activity", "fold",
)
NEGATIVE_KWS = ("decrease", "decreased", "reduced", "lower", "loss", "worse")

TEMP_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:degc|c)\b", re.IGNORECASE)
PH_RE = re.compile(r"\bpH\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
FOLD_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*[- ]?fold\b", re.IGNORECASE)

SUBSTRATE_KWS = ("pet", "bhet", "mhet", "pcl", "pet-np", "pet-bp")


def load_docs(meta_path: Path) -> List[dict]:
    docs = []
    with meta_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))
    return docs


def normalize_variant(token: str) -> str:
    cleaned = token.replace(" ", "")
    return cleaned


def extract_candidates(text: str) -> List[str]:
    candidates = set()
    for match in COMBO_MUTATION_RE.findall(text):
        candidates.add(match)
    for match in MUTATION_RE.findall(text):
        candidates.add(match)
    if IS_PETASE_RE.search(text):
        candidates.add("IsPETase")
    for match in PETASE_RE.findall(text):
        token = normalize_variant(match)
        if token.lower() == "petase":
            continue
        candidates.add(token)
    return sorted(candidates)


def window_claims(text: str, start: int, end: int) -> str:
    left = max(0, start - 200)
    right = min(len(text), end + 200)
    return text[left:right]


def extract_conditions(text: str) -> List[str]:
    conditions = []
    for match in TEMP_RE.findall(text):
        conditions.append(f"{match} C")
    for match in PH_RE.findall(text):
        conditions.append(f"pH {match}")
    lowered = text.lower()
    for kw in SUBSTRATE_KWS:
        if kw in lowered:
            conditions.append(kw.upper())
    return conditions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace with an existing vector store.")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    vector_dir = args.workspace.resolve() / "vector_store"
    meta_path = vector_dir / "metadata.jsonl"
    if not meta_path.exists():
        raise SystemExit("Vector store metadata not found.")

    docs = load_docs(meta_path)
    if not docs:
        raise SystemExit("No documents found in metadata.")

    stats = defaultdict(lambda: {
        "evidence_count": 0,
        "papers": set(),
        "citations": set(),
        "positive_papers": set(),
        "negative_papers": set(),
        "folds": [],
        "conditions": Counter(),
        "display": None,
    })

    for doc in docs:
        text = doc.get("text", "")
        meta = doc.get("metadata", {})
        chunk_id = meta.get("chunk_id") or str(doc.get("id") or "")
        paper = meta.get("pdf_file") or meta.get("title") or "unknown"
        candidates = extract_candidates(text)
        if not candidates:
            continue
        for candidate in candidates:
            entry = stats[candidate.lower()]
            entry["display"] = entry["display"] or candidate
            entry["evidence_count"] += 1
            entry["papers"].add(paper)
            entry["citations"].add(chunk_id)

            for match in re.finditer(re.escape(candidate), text, flags=re.IGNORECASE):
                window = window_claims(text, match.start(), match.end()).lower()
                if any(kw in window for kw in POSITIVE_KWS):
                    entry["positive_papers"].add(paper)
                    fold_match = FOLD_RE.search(window)
                    if fold_match:
                        entry["folds"].append(f"{fold_match.group(1)}-fold")
                if any(kw in window for kw in NEGATIVE_KWS):
                    entry["negative_papers"].add(paper)
                for cond in extract_conditions(window):
                    entry["conditions"][cond] += 1

    ranked = []
    for key, entry in stats.items():
        if not entry["display"]:
            continue
        replication_count = len(entry["positive_papers"])
        contradiction = bool(entry["positive_papers"] and entry["negative_papers"])
        condition_parts = [c for c, _ in entry["conditions"].most_common(3)]
        improvement_summary = "reported improved" if entry["positive_papers"] else "no improvement claim found"
        if entry["folds"]:
            improvement_summary = f"reported {Counter(entry['folds']).most_common(1)[0][0]} improvement"
        ranked.append({
            "candidate": entry["display"],
            "evidence_count": entry["evidence_count"],
            "paper_count": len(entry["papers"]),
            "replication_count": replication_count,
            "assay_condition_summary": ", ".join(condition_parts) if condition_parts else "not reported",
            "improvement_summary": improvement_summary,
            "contradiction_flags": contradiction,
            "citations": sorted(entry["citations"]),
        })

    ranked.sort(
        key=lambda item: (item["replication_count"], item["paper_count"], item["evidence_count"]),
        reverse=True,
    )
    top = ranked[: args.top]

    report_lines = [
        "# Top candidates report",
        f"Generated: {datetime.utcnow().isoformat()}Z",
        "",
    ]
    for idx, item in enumerate(top, start=1):
        rationale = (
            f"evidence={item['evidence_count']}, papers={item['paper_count']}, "
            f"replication={item['replication_count']}"
        )
        report_lines.append(f"{idx}. {item['candidate']}")
        report_lines.append(f"   - rationale: {rationale}")
        report_lines.append(f"   - assay conditions: {item['assay_condition_summary']}")
        report_lines.append(f"   - improvement: {item['improvement_summary']}")
        report_lines.append(f"   - contradiction: {item['contradiction_flags']}")
        report_lines.append(f"   - citations: {', '.join(item['citations'])}")
        report_lines.append("")

    output_dir = QA_OUTPUT_ROOT / args.workspace.name / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "top10_candidates.json").write_text(json.dumps(top, indent=2, ensure_ascii=True))
    report_text = "\n".join(report_lines).encode("ascii", "backslashreplace").decode("ascii")
    (output_dir / "top10_candidates.md").write_text(report_text, encoding="ascii")

    print(f"Wrote top {len(top)} candidates.")


if __name__ == "__main__":
    main()
