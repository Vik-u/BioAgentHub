#!/usr/bin/env python3
"""Parse device PDF text into structured chunks keyed by leading markers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


def parse_chunks(raw: str) -> List[Dict[str, str]]:
    """
    Split text into chunks where a header line begins with '//' or '\\\\'.
    Returns a list of {header, body}.
    """
    lines = raw.splitlines()
    chunks: List[Dict[str, str]] = []
    header = None
    body: List[str] = []

    def push():
        nonlocal header, body
        if header is not None:
            # Remove lines that are only braces/whitespace to avoid "\t { \t" bodies.
            filtered = [ln for ln in body if any(ch.isalnum() for ch in ln)]
            body_text = "\n".join(filtered).strip()
            # Skip chunks that have no alphanumeric content.
            if body_text and any(ch.isalnum() for ch in body_text):
                chunks.append({"header": header.strip(), "body": body_text})
        header = None
        body = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("\\\\"):
            # New header
            push()
            header = stripped
        else:
            body.append(line)
    push()
    return [c for c in chunks if c["header"] or c["body"]]


def process_all(src_dir: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for json_file in sorted(src_dir.glob("*.json")):
        if json_file.name == "index.json":
            continue
        data = json.loads(json_file.read_text())
        text = data.get("text") or ""
        chunks = parse_chunks(text)
        out = {
            "pdf_file": data.get("pdf_file"),
            "page_count": data.get("page_count"),
            "chunks": chunks,
        }
        out_path = dest_dir / json_file.name
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))
        index.append({"source": json_file.name, "out_file": str(out_path), "chunk_count": len(chunks)})
    (dest_dir / "index.json").write_text(json.dumps(index, indent=2))
    print(f"Structured {len(index)} files -> {dest_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=Path("Devices/text_json"), help="Input JSON dir from PDF extraction.")
    parser.add_argument("--dest", type=Path, default=Path("Devices/text_structured"), help="Output dir for structured chunks.")
    args = parser.parse_args()
    process_all(args.src, args.dest)


if __name__ == "__main__":
    main()
