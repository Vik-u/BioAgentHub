#!/usr/bin/env python3
"""Extract structured experimental protocol steps from methodology JSON files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
METH_DIR = ROOT / "KnowledgeGraph" / "methodology"
META_DIR = ROOT / "KnowledgeGraph" / "metadata"
OUT_DIR = ROOT / "KnowledgeGraph" / "protocols"


def load_title_map() -> dict:
    title_map = {}
    if META_DIR.exists():
        for meta_file in META_DIR.glob("*.json"):
            try:
                data = json.loads(meta_file.read_text())
            except Exception:
                continue
            pdf = data.get("pdf_file")
            title = data.get("title_candidate") or meta_file.stem
            if pdf:
                title_map[pdf] = title
    return title_map


def split_steps(text: str) -> List[str]:
    text = text.replace("\r", " ")
    candidates = re.split(r"\n+|\.\s+", text)
    steps: List[str] = []
    for cand in candidates:
        cleaned = cand.strip()
        if not cleaned:
            continue
        if len(cleaned) < 15:
            continue
        if not re.search(r"(add|incubate|centrifuge|mix|measure|culture|inoculate|dry|wash|adjust|record)", cleaned, re.I):
            continue
        steps.append(cleaned)
    return steps


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    title_map = load_title_map()
    count = 0
    for meth_file in sorted(METH_DIR.glob("*.json")):
        data = json.loads(meth_file.read_text())
        pdf_txt = data.get("txt_file")
        pdf_name = (Path(pdf_txt).stem + ".pdf") if pdf_txt else None
        sections = data.get("experimental_sections") or []
        if not sections:
            continue
        all_steps: List[str] = []
        for section in sections:
            all_steps.extend(split_steps(section))
        if not all_steps:
            continue
        payload = {
            "pdf_file": pdf_name,
            "title": title_map.get(pdf_name, pdf_name or meth_file.stem),
            "steps": all_steps,
        }
        out_file = OUT_DIR / f"{meth_file.stem}.json"
        out_file.write_text(json.dumps(payload, indent=2))
        count += 1
    print(f"Protocol files written: {count}")


if __name__ == "__main__":
    main()
