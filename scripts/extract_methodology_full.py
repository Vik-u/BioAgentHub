#!/usr/bin/env python3
"""Extract full experimental/computational/results sections from PETase texts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

TEXT_DIR = Path("KnowledgeGraph/text")
META_INDEX = Path("KnowledgeGraph/corpus_index.json")
OUT_DIR = Path("KnowledgeGraph/methodology_full")

EXP_KEYWORDS = [
    "materials and methods",
    "material and methods",
    "experimental",
    "methods",
    "methodology",
    "wet lab",
    "experimental procedures",
]
COMP_KEYWORDS = [
    "computational",
    "in silico",
    "simulation",
    "molecular dynamics",
    "quantum",
    "qm/mm",
    "modeling",
    "bioinformatics",
]
RESULT_KEYWORDS = [
    "results",
    "discussion",
    "findings",
    "conclusion",
    "outcome",
]

STOP_HEADINGS = [
    "references",
    "acknowledgments",
    "supplementary",
    "supporting",
]

HEADING_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)*)?\s*[A-Z][A-Za-z0-9\s\-,:()]+$")


def load_meta_map() -> Dict[str, dict]:
    if not META_INDEX.exists():
        return {}
    data = json.loads(META_INDEX.read_text())
    return {entry["txt_file"]: entry for entry in data}


def is_heading(line: str) -> bool:
    text = line.strip()
    if not text or len(text) > 180:
        return False
    if text.endswith(":"):
        return True
    if text.isupper():
        return True
    if HEADING_PATTERN.match(text):
        return True
    words = text.split()
    if len(words) <= 2:
        return False
    uppercase_ratio = sum(1 for ch in text if ch.isupper()) / max(len(text), 1)
    return uppercase_ratio > 0.55


def categorize_heading(text: str) -> str | None:
    lower = text.lower()
    for kw in EXP_KEYWORDS:
        if kw in lower:
            return "experimental"
    for kw in COMP_KEYWORDS:
        if kw in lower:
            return "computational"
    for kw in RESULT_KEYWORDS:
        if kw in lower:
            return "results"
    for kw in STOP_HEADINGS:
        if kw in lower:
            return "stop"
    return None


def extract_sections(text: str) -> Dict[str, List[dict]]:
    lines = text.splitlines()
    sections: Dict[str, List[dict]] = {"experimental": [], "computational": [], "results": []}
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if not is_heading(line):
            idx += 1
            continue
        category = categorize_heading(line)
        idx += 1
        body: List[str] = []
        while idx < len(lines):
            next_line = lines[idx]
            if is_heading(next_line):
                next_category = categorize_heading(next_line)
                if next_category in {"experimental", "computational", "results", "stop"}:
                    break
            body.append(next_line)
            idx += 1
        if category in {"experimental", "computational", "results"}:
            content = "\n".join(body).strip()
            if len(content) >= 200:
                sections[category].append({"heading": line.strip(), "text": content})
    return sections


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text-dir", type=Path, default=TEXT_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    meta_map = load_meta_map()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for txt_path in sorted(args.text_dir.glob("*.txt")):
        text = txt_path.read_text(errors="ignore")
        sections = extract_sections(text)
        if not any(sections.values()):
            continue
        meta = meta_map.get(txt_path.name, {})
        payload = {
            "txt_file": txt_path.name,
            "pdf_file": meta.get("pdf_file"),
            "title": meta.get("title_candidate"),
            "experimental_sections": sections["experimental"],
            "computational_sections": sections["computational"],
            "results_sections": sections["results"],
        }
        out_path = args.output_dir / f"{txt_path.stem}.json"
        out_path.write_text(json.dumps(payload, indent=2))
        count += 1
    print(f"Wrote methodology sections for {count} texts to {args.output_dir}")


if __name__ == "__main__":
    main()
