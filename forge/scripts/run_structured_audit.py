#!/usr/bin/env python3
"""Run structured extraction upgrades and generate audit reports."""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from utils.output_paths import reports_dir  # noqa: E402
DEFAULT_TOPICS = ["petase", "3hp_pand", "retron"]


def load_jsonl(path: Path) -> List[dict]:
    rows = []
    if not path.exists():
        return rows
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def ensure_reports_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_step(cmd: List[str]) -> None:
    subprocess.run(cmd, check=True)


def confidence_bins(facts: List[dict]) -> Dict[str, int]:
    bins = {
        "0.0-0.2": 0,
        "0.2-0.4": 0,
        "0.4-0.6": 0,
        "0.6-0.8": 0,
        "0.8-1.0": 0,
    }
    for fact in facts:
        conf = fact.get("confidence")
        if not isinstance(conf, (int, float)):
            continue
        if conf < 0.2:
            bins["0.0-0.2"] += 1
        elif conf < 0.4:
            bins["0.2-0.4"] += 1
        elif conf < 0.6:
            bins["0.4-0.6"] += 1
        elif conf < 0.8:
            bins["0.6-0.8"] += 1
        else:
            bins["0.8-1.0"] += 1
    return bins


def top_entities(facts: List[dict], limit: int = 20) -> List[Tuple[str, int]]:
    counts = Counter()
    for fact in facts:
        head = fact.get("head", {}).get("norm")
        tail = fact.get("tail", {}).get("norm")
        if head:
            counts[head] += 1
        if tail:
            counts[tail] += 1
    return counts.most_common(limit)


def find_duplicates(facts: List[dict]) -> Dict[str, object]:
    exact_counts = Counter()
    for fact in facts:
        key = (
            fact.get("head", {}).get("norm"),
            fact.get("relation_type"),
            fact.get("tail", {}).get("norm"),
            fact.get("provenance", {}).get("pdf"),
            fact.get("provenance", {}).get("page"),
        )
        exact_counts[key] += 1
    exact_dupes = [key for key, count in exact_counts.items() if count > 1]

    near_dupes = []
    grouped = defaultdict(list)
    for fact in facts:
        key = (fact.get("head", {}).get("norm"), fact.get("relation_type"))
        grouped[key].append(fact)
    for key, group in grouped.items():
        if len(group) > 30:
            group = group[:30]
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a = group[i].get("evidence_text", "")
                b = group[j].get("evidence_text", "")
                if not a or not b:
                    continue
                score = SequenceMatcher(None, a, b).ratio()
                if score >= 0.9:
                    near_dupes.append(
                        {
                            "head": key[0],
                            "relation_type": key[1],
                            "similarity": round(score, 3),
                            "evidence_a": a[:200],
                            "evidence_b": b[:200],
                        }
                    )
                if len(near_dupes) >= 20:
                    break
            if len(near_dupes) >= 20:
                break
        if len(near_dupes) >= 20:
            break

    return {
        "exact_duplicate_count": len(exact_dupes),
        "exact_duplicate_keys": exact_dupes[:20],
        "near_duplicates_sample": near_dupes,
    }


def sample_facts(facts: List[dict], sample_size: int, seed: int) -> List[dict]:
    random.seed(seed)
    by_relation = defaultdict(list)
    for fact in facts:
        by_relation[fact.get("relation_type")].append(fact)
    samples = []
    relation_types = sorted(by_relation.keys())
    while len(samples) < sample_size and relation_types:
        for relation in relation_types:
            if len(samples) >= sample_size:
                break
            bucket = by_relation[relation]
            if not bucket:
                continue
            samples.append(bucket.pop(random.randrange(len(bucket))))
        relation_types = [rel for rel in relation_types if by_relation[rel]]
    return samples


def build_report(topic: str, facts: List[dict], artifacts_summary: Dict[str, object]) -> Dict[str, object]:
    relation_counts = Counter([fact.get("relation_type") for fact in facts if fact.get("relation_type")])
    source_counts = Counter([fact.get("provenance", {}).get("source") for fact in facts])
    report = {
        "topic": topic,
        "fact_count": len(facts),
        "relation_counts": relation_counts.most_common(),
        "confidence_distribution": confidence_bins(facts),
        "top_entities": top_entities(facts),
        "duplicates": find_duplicates(facts),
        "structured_coverage": {
            "captions": artifacts_summary.get("caption_count", 0),
            "tables": artifacts_summary.get("table_count", 0),
            "facts_by_source": dict(source_counts),
        },
        "facts_sample": sample_facts(facts, 50, seed=7),
    }
    return report


def write_report(report_dir: Path, topic: str, report: Dict[str, object]) -> None:
    ensure_reports_dir(report_dir)
    json_path = report_dir / f"{topic}_report.json"
    md_path = report_dir / f"{topic}_report.md"
    json_path.write_text(json.dumps(report, indent=2))

    lines = [
        f"# Structured KG Audit - {topic}",
        "",
        f"- Fact count: {report['fact_count']}",
        f"- Captions extracted: {report['structured_coverage']['captions']}",
        f"- Tables extracted: {report['structured_coverage']['tables']}",
        "",
        "## Relation Counts",
    ]
    for rel, count in report["relation_counts"]:
        lines.append(f"- {rel}: {count}")
    lines.append("")
    lines.append("## Confidence Distribution")
    for bucket, count in report["confidence_distribution"].items():
        lines.append(f"- {bucket}: {count}")
    lines.append("")
    lines.append("## Top Entities")
    for entity, count in report["top_entities"]:
        lines.append(f"- {entity}: {count}")
    lines.append("")
    lines.append("## Duplicates")
    lines.append(f"- Exact duplicate keys: {report['duplicates']['exact_duplicate_count']}")
    lines.append("")
    lines.append("## Sample Facts")
    for fact in report["facts_sample"][:10]:
        head = fact.get("head", {}).get("norm")
        rel = fact.get("relation_type")
        tail = fact.get("tail", {}).get("norm")
        lines.append(f"- {head} {rel} {tail}")
    md_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topics", nargs="*", default=DEFAULT_TOPICS, help="Topics to process.")
    parser.add_argument("--workspace-root", type=Path, default=PROJECT_ROOT / "workspaces")
    parser.add_argument("--pdf-root", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument("--report-dir", type=Path, default=reports_dir() / "structured_audit")
    parser.add_argument("--max-pdfs", type=int, help="Process only first N PDFs per topic.")
    parser.add_argument("--limit-pdfs", type=int, help="Alias for --max-pdfs.")
    parser.add_argument("--max-pages", type=int, help="Process only first N pages per PDF.")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR fallback.")
    parser.add_argument("--artifacts-root", type=Path, help="Override artifacts root folder.")
    parser.add_argument("--facts-root", type=Path, help="Override facts output root folder.")
    args = parser.parse_args()

    report_dir = args.report_dir.resolve()
    combined_facts = []
    combined_artifacts = {"caption_count": 0, "table_count": 0}

    for topic in args.topics:
        workspace = (args.workspace_root / topic).resolve()
        pdf_dir = (args.pdf_root / topic).resolve()
        artifacts_dir = (args.artifacts_root / topic) if args.artifacts_root else (workspace / "artifacts")
        facts_dir = (args.facts_root / topic) if args.facts_root else (workspace / "facts")
        facts_path = facts_dir / "facts.jsonl"

        max_pdfs = args.max_pdfs if args.max_pdfs is not None else args.limit_pdfs
        run_step(
            [
                sys.executable,
                str(PROJECT_ROOT / "forge" / "scripts" / "extract_pdf_artifacts.py"),
                "--workspace",
                str(workspace),
                "--pdf-dir",
                str(pdf_dir),
                "--out-dir",
                str(artifacts_dir),
                *(["--max-pdfs", str(max_pdfs)] if max_pdfs else []),
                *(["--max-pages", str(args.max_pages)] if args.max_pages else []),
                *(["--no-ocr"] if args.no_ocr else []),
            ]
        )
        run_step(
            [
                sys.executable,
                str(PROJECT_ROOT / "forge" / "scripts" / "build_structured_facts.py"),
                "--workspace",
                str(workspace),
                "--artifacts-dir",
                str(artifacts_dir),
                "--out-path",
                str(facts_path),
            ]
        )

        facts = load_jsonl(facts_path)
        artifacts_summary_path = artifacts_dir / "summary.json"
        artifacts_summary = json.loads(artifacts_summary_path.read_text()) if artifacts_summary_path.exists() else {}
        report = build_report(topic, facts, artifacts_summary)
        write_report(report_dir, topic, report)
        combined_facts.extend(facts)
        combined_artifacts["caption_count"] += artifacts_summary.get("caption_count", 0)
        combined_artifacts["table_count"] += artifacts_summary.get("table_count", 0)

    combined_report = build_report("combined", combined_facts, combined_artifacts)
    write_report(report_dir, "combined", combined_report)


if __name__ == "__main__":
    main()
