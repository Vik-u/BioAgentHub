#!/usr/bin/env python3
"""Convenience wrapper to build a generic workspace from PDFs."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True, help="Folder containing PDFs.")
    parser.add_argument("--workspace", type=Path, required=True, help="Target workspace directory.")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    run(["python", "scripts/generic_extract_corpus.py", "--pdf-dir", str(args.pdf_dir), "--workspace", str(workspace)])
    run(["python", "scripts/generic_build_vector_store.py", "--workspace", str(workspace), "--model", args.model])
    print(f"Workspace ready at {workspace}")


if __name__ == "__main__":
    main()
