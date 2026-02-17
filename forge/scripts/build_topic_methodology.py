#!/usr/bin/env python3
"""
Build per-topic methodology assets (sections + KG + vector stores) for a workspace.

Example:
  python forge/scripts/build_topic_methodology.py --workspace workspaces/retron
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace root.")
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model for methodology vector stores.",
    )
    parser.add_argument(
        "--embedding-backend",
        default="sentence-transformers",
        help="Embedding backend: sentence-transformers or openai.",
    )
    parser.add_argument("--no-faiss", action="store_true", help="Skip FAISS index build.")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    method_dir = workspace / "methodology_full"
    edges_path = workspace / "methodology_kg_edges.jsonl"
    summary_path = workspace / "methodology_kg_summary.json"
    edge_store = workspace / "methodology_edge_store"
    vector_store = workspace / "methodology_vector_store"

    run(
        [
            sys.executable,
            "forge/scripts/extract_methodology_full.py",
            "--workspace",
            str(workspace),
        ]
    )

    run(
        [
            sys.executable,
            "forge/scripts/build_methodology_kg.py",
            "--workspace",
            str(workspace),
        ]
    )

    edge_cmd = [
        sys.executable,
        "forge/scripts/build_methodology_edge_store.py",
        "--edges",
        str(edges_path),
        "--out-dir",
        str(edge_store),
        "--model",
        args.model,
        "--embedding-backend",
        args.embedding_backend,
    ]
    if args.no_faiss:
        edge_cmd.append("--no-faiss")
    run(edge_cmd)

    vec_cmd = [
        sys.executable,
        "forge/scripts/build_methodology_vector_store.py",
        "--method-dir",
        str(method_dir),
        "--out-dir",
        str(vector_store),
        "--model",
        args.model,
        "--embedding-backend",
        args.embedding_backend,
    ]
    if args.no_faiss:
        vec_cmd.append("--no-faiss")
    run(vec_cmd)

    print(f"=== Methodology assets ready under {workspace}")


if __name__ == "__main__":
    main()
