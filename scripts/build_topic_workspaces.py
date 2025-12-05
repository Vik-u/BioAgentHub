#!/usr/bin/env python3
"""Build per-topic and combined generic workspaces from data folders."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERIC_EXTRACT = PROJECT_ROOT / "scripts" / "generic_extract_corpus.py"
GENERIC_VECTOR = PROJECT_ROOT / "scripts" / "generic_build_vector_store.py"


def run(cmd: List[str]) -> None:
    """Print and execute a subprocess command."""
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def pdf_count(root: Path) -> int:
    return len(list(root.rglob("*.pdf")))


def iter_topic_dirs(data_root: Path) -> Iterable[Path]:
    for path in sorted(data_root.iterdir()):
        if path.is_dir():
            yield path


def build_workspace(pdf_dir: Path, workspace: Path, model: str, export_images: bool) -> None:
    workspace = workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    extract_cmd = [
        sys.executable,
        str(GENERIC_EXTRACT),
        "--pdf-dir",
        str(pdf_dir),
        "--workspace",
        str(workspace),
    ]
    if export_images:
        extract_cmd.append("--export-images")
    run(extract_cmd)

    run(
        [
            sys.executable,
            str(GENERIC_VECTOR),
            "--workspace",
            str(workspace),
            "--model",
            model,
        ]
    )


def bundle_pdfs(sources: List[Path], dest: Path) -> int:
    """Symlink (or copy) PDFs from multiple folders into dest; returns file count."""
    dest.mkdir(parents=True, exist_ok=True)
    added = 0
    for src in sources:
        topic = src.name
        for pdf_path in sorted(src.rglob("*.pdf")):
            name = f"{topic}__{pdf_path.name}"
            target = dest / name
            suffix = 1
            while target.exists():
                target = dest / f"{topic}__{suffix}_{pdf_path.name}"
                suffix += 1
            try:
                target.symlink_to(pdf_path.resolve())
            except OSError:
                shutil.copy2(pdf_path, target)
            added += 1
    return added


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=PROJECT_ROOT / "data",
        help="Root folder containing topic subfolders (each with PDFs).",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=PROJECT_ROOT / "workspaces",
        help="Where to write per-topic workspaces.",
    )
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model to use for embeddings.",
    )
    parser.add_argument(
        "--petase-main",
        type=Path,
        default=PROJECT_ROOT / "Papers",
        help="Optional main PETase PDF dir to merge with data/petase for a petase_full workspace.",
    )
    parser.add_argument(
        "--skip-combined",
        action="store_true",
        help="Disable building the all_topics combined workspace.",
    )
    parser.add_argument(
        "--export-images",
        action="store_true",
        help="Render page PNGs during extraction (debug/QA).",
    )
    args = parser.parse_args()

    if not args.data_root.exists():
        raise SystemExit(f"Data root not found: {args.data_root}")
    topics = list(iter_topic_dirs(args.data_root))
    if not topics:
        raise SystemExit(f"No topic folders found under {args.data_root}")

    summary: Dict[str, Tuple[int, Path]] = {}
    for topic_dir in topics:
        ws_path = args.workspace_root / topic_dir.name
        count = pdf_count(topic_dir)
        build_workspace(topic_dir, ws_path, args.model, args.export_images)
        summary[topic_dir.name] = (count, ws_path)

    # petase_full merges existing Papers with data/petase if both are available.
    petase_topic = args.data_root / "petase"
    if petase_topic.exists() and args.petase_main.exists():
        with tempfile.TemporaryDirectory(prefix="petase_full_") as tmpdir:
            bundle = Path(tmpdir)
            merged_count = bundle_pdfs([args.petase_main, petase_topic], bundle)
            ws_path = args.workspace_root / "petase_full"
            build_workspace(bundle, ws_path, args.model, args.export_images)
            summary["petase_full"] = (merged_count, ws_path)

    # Combined workspace across all topics (and Papers if present).
    if not args.skip_combined:
        sources = topics.copy()
        if args.petase_main.exists():
            sources.append(args.petase_main)
        with tempfile.TemporaryDirectory(prefix="all_topics_") as tmpdir:
            bundle = Path(tmpdir)
            combined_count = bundle_pdfs(sources, bundle)
            ws_path = args.workspace_root / "all_topics"
            build_workspace(bundle, ws_path, args.model, args.export_images)
            summary["all_topics"] = (combined_count, ws_path)

    print("\nWorkspaces built:")
    for name, (count, path) in sorted(summary.items()):
        print(f"- {name}: {count} PDFs -> {path}")


if __name__ == "__main__":
    main()
