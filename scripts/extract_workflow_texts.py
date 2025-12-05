#!/usr/bin/env python3
"""Copy Momentum workflow .txt files into JSON for retrieval."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def find_texts(root: Path):
    return sorted(p for p in root.rglob("*.txt") if p.is_file())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflows-dir", type=Path, default=Path("Devices/Workflows"))
    parser.add_argument("--out-dir", type=Path, default=Path("Devices/workflow_json"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for txt in find_texts(args.workflows_dir):
        text = txt.read_text(encoding="utf-8", errors="ignore")
        payload = {"workflow_file": str(txt), "text": text}
        out_path = args.out_dir / (txt.stem.replace("/", "_") + ".json")
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        index.append({"workflow_file": str(txt), "json_file": str(out_path)})
    (args.out_dir / "index.json").write_text(json.dumps(index, indent=2))
    print(f"Extracted {len(index)} workflow txt files → {args.out_dir}")


if __name__ == "__main__":
    main()
