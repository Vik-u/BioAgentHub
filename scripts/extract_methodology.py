#!/usr/bin/env python3
"""Extract experimental/computational methodology snippets from corpus text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

TRIGGERS = {
    "experimental": [
        "materials and methods",
        "material and methods",
        "experimental section",
        "experimental procedures",
        "methodology",
        "experimental methods",
    ],
    "computational": [
        "computational methods",
        "in silico",
        "simulation",
        "molecular dynamics",
        "quantum",
        "dft",
        "modeling",
        "in silico design",
    ],
}


def _is_heading(line: str) -> bool:
    text = line.strip()
    if not text or len(text) > 120:
        return False
    if text.endswith(":"):
        return True
    words = text.split()
    if len(words) < 2 or len(words) > 12:
        return False
    uppercase_ratio = sum(1 for ch in text if ch.isupper()) / max(len(text), 1)
    return uppercase_ratio > 0.6


def extract_blocks(text: str, keywords: List[str]) -> List[str]:
    lines = text.splitlines()
    blocks: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        lower = line.lower()
        normalized = lower.strip().lstrip("0123456789. )(")
        if any(keyword in lower for keyword in keywords) and (
            _is_heading(line)
            or normalized.startswith(tuple(keyword for keyword in keywords))
            or (i > 0 and not lines[i - 1].strip())
        ):
            start = i
            j = i + 1
            while j < len(lines):
                if _is_heading(lines[j]):
                    break
                j += 1
            block = "\n".join(lines[start:j]).strip()
            if block:
                blocks.append(block)
            i = j
        else:
            i += 1
    return blocks


def detect_sections(text: str) -> Dict[str, List[str]]:
    return {
        "experimental": extract_blocks(text, TRIGGERS["experimental"]),
        "computational": extract_blocks(text, TRIGGERS["computational"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--text-dir",
        type=Path,
        default=Path("KnowledgeGraph/text"),
        help="Directory containing extracted text files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("KnowledgeGraph/methodology"),
        help="Directory to store methodology snippets.",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for txt_path in sorted(args.text_dir.glob("*.txt")):
        text = txt_path.read_text(errors="ignore")
        sections = detect_sections(text)
        payload = {
            "txt_file": txt_path.name,
            "experimental_sections": sections["experimental"],
            "computational_sections": sections["computational"],
        }
        if payload["experimental_sections"] or payload["computational_sections"]:
            out_file = args.output_dir / f"{txt_path.stem}.json"
            out_file.write_text(json.dumps(payload, indent=2))

    print(f"Methodology snippets stored in {args.output_dir}")


if __name__ == "__main__":
    main()
