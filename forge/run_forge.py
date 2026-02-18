#!/usr/bin/env python3
"""Forge: end-to-end IE + KG build across topics (PDFs -> KG artifacts)."""

from __future__ import annotations

import argparse
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from utils.output_paths import reports_dir  # noqa: E402
DEFAULT_TOPICS = ["petase", "3hp_pand", "retron"]


def run(cmd: List[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def format_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}B"


def format_mtime(epoch: float) -> str:
    return datetime.datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")


def artifact_status(paths: Sequence[Path], size_path: Path) -> Tuple[bool, str]:
    if all(path.exists() for path in paths):
        stat = size_path.stat()
        return True, f"OK {format_size(stat.st_size)} {format_mtime(stat.st_mtime)}"
    return False, "MISSING"


def collect_workspace_outputs(workspace: Path) -> Dict[str, Path]:
    return {
        "schema": workspace / "kg_schema.json",
        "facts": workspace / "facts",
        "edges": workspace / "kg_edges.jsonl",
        "graph_overview": workspace / "graph_overview.json",
        "graph": workspace / "graph.sqlite",
        "kg_vector_store": workspace / "kg_vector_store",
        "vector_store": workspace / "vector_store",
    }


def collect_report_outputs(report_dir: Path, topic: str, include_combined: bool) -> Dict[str, Path]:
    outputs = {
        "topic_json": report_dir / f"{topic}_report.json",
        "topic_md": report_dir / f"{topic}_report.md",
    }
    if include_combined:
        outputs["combined_json"] = report_dir / "combined_report.json"
        outputs["combined_md"] = report_dir / "combined_report.md"
    return outputs


def load_schema_induction_config(project_root: Path) -> Dict[str, object]:
    config_path = project_root / "config" / "llm_config.json"
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text())
    except json.JSONDecodeError:
        return {}


def ensure_pydantic_ai_available(config: Dict[str, object]) -> None:
    backend = str(config.get("schema_induction_backend") or "").lower()
    if backend != "pydantic_ai":
        return
    try:
        import pydantic_ai  # noqa: F401
    except Exception as exc:
        raise SystemExit(
            "schema_induction_backend=pydantic_ai but pydantic_ai is not installed in this environment. "
            "Install it with: python -m pip install pydantic-ai-slim[openai]==0.0.18"
        ) from exc


def schema_matches_config(workspace: Path, config: Dict[str, object]) -> Tuple[bool, str]:
    schema_path = workspace / "kg_schema.json"
    if not schema_path.exists():
        return False, "schema missing"
    try:
        payload = json.loads(schema_path.read_text())
    except json.JSONDecodeError:
        return False, "schema unreadable"
    version = payload.get("schema_version") or {}
    expected_backend = str(config.get("schema_induction_backend") or "").lower()
    expected_model = str(config.get("schema_induction_model") or config.get("model") or "")
    expected_seed = int(config.get("schema_induction_seed", 7) or 7)
    backend_ok = not expected_backend or str(version.get("backend", "")).lower() == expected_backend
    model_ok = not expected_model or str(version.get("model", "")) == expected_model
    seed_ok = str(version.get("seed", expected_seed)) == str(expected_seed)
    if backend_ok and model_ok and seed_ok:
        return True, "config match"
    return False, f"config mismatch (backend={version.get('backend')}, model={version.get('model')}, seed={version.get('seed')})"


def archive_outputs(
    workspace: Path,
    report_dir: Path,
    outputs: Sequence[Path],
    report_outputs: Sequence[Path],
    delete_old: bool,
) -> Optional[Path]:
    existing = [path for path in outputs if path.exists()]
    existing_reports = [path for path in report_outputs if path.exists()]
    if not existing and not existing_reports:
        return None

    if delete_old:
        for path in existing + existing_reports:
            remove_path(path)
        return None

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S%f")
    archive_dir = workspace / "archives" / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)

    for path in existing:
        dest = archive_dir / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))

    if existing_reports:
        report_archive_dir = archive_dir / "reports" / "structured_audit"
        report_archive_dir.mkdir(parents=True, exist_ok=True)
        for path in existing_reports:
            dest = report_archive_dir / path.name
            shutil.move(str(path), str(dest))

    return archive_dir


def print_status_table(rows: List[Dict[str, str]]) -> None:
    if not rows:
        print("No topics to report.")
        return
    columns = ["topic", "schema", "facts", "edges", "graph", "audit", "vector_store", "kg_vector_store"]
    widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            widths[col] = max(widths[col], len(row.get(col, "")))
    header = "  ".join(col.ljust(widths[col]) for col in columns)
    divider = "  ".join("-" * widths[col] for col in columns)
    print(header)
    print(divider)
    for row in rows:
        print("  ".join(row.get(col, "").ljust(widths[col]) for col in columns))


def verify_outputs(
    topics: Sequence[str],
    workspace_root: Path,
    report_dir: Path,
) -> int:
    rows = []
    missing_required = False
    for topic in topics:
        workspace = workspace_root / topic
        outputs = collect_workspace_outputs(workspace)
        reports = collect_report_outputs(report_dir, topic, include_combined=False)

        schema_ok, schema_status = artifact_status([outputs["schema"]], outputs["schema"])
        facts_path = outputs["facts"] / "facts.jsonl"
        facts_ok, facts_status = artifact_status([facts_path], facts_path) if facts_path.exists() else (False, "MISSING")
        edges_ok, edges_status = artifact_status([outputs["edges"], outputs["graph_overview"]], outputs["edges"])
        graph_ok, graph_status = artifact_status([outputs["graph"]], outputs["graph"])
        audit_ok, audit_status = artifact_status([reports["topic_json"], reports["topic_md"]], reports["topic_json"])

        vector_path = outputs["vector_store"] / "config.json"
        if vector_path.exists():
            vector_ok, vector_status = artifact_status([vector_path], vector_path)
        else:
            vector_ok, vector_status = False, "MISSING (optional)"
        kg_vector_path = outputs["kg_vector_store"] / "config.json"
        if kg_vector_path.exists():
            kg_vector_ok, kg_vector_status = artifact_status([kg_vector_path], kg_vector_path)
        else:
            kg_vector_ok, kg_vector_status = False, "MISSING (optional)"

        rows.append(
            {
                "topic": topic,
                "schema": schema_status,
                "facts": facts_status,
                "edges": edges_status,
                "graph": graph_status,
                "audit": audit_status,
                "vector_store": vector_status,
                "kg_vector_store": kg_vector_status,
            }
        )
        if not all([schema_ok, facts_ok, edges_ok, graph_ok, audit_ok]):
            missing_required = True

    print_status_table(rows)
    return 1 if missing_required else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topics", nargs="*", default=DEFAULT_TOPICS, help="Topics to process.")
    parser.add_argument("--workspace-root", type=Path, default=PROJECT_ROOT / "workspaces")
    parser.add_argument("--pdf-root", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument("--report-dir", type=Path, default=reports_dir() / "structured_audit")
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model for text vector stores.",
    )
    parser.add_argument(
        "--embedding-backend",
        default="sentence-transformers",
        help="Embedding backend for text vectors (sentence-transformers or openai).",
    )
    parser.add_argument(
        "--kg-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model for KG edge vector stores.",
    )
    parser.add_argument(
        "--kg-embedding-backend",
        default="sentence-transformers",
        help="Embedding backend for KG edge vectors (sentence-transformers or openai).",
    )
    parser.add_argument(
        "--focus-query",
        default="protein engineering",
        help="Focus query used by the schema agent.",
    )
    parser.add_argument("--max-pdfs", type=int, help="Process only first N PDFs per topic (audit stage).")
    parser.add_argument("--limit-pdfs", type=int, help="Alias for --max-pdfs.")
    parser.add_argument("--max-pages", type=int, help="Process only first N pages per PDF (audit stage).")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR fallback (audit stage).")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verification only: check artifact presence and exit without rebuilding.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip rebuild steps when outputs already exist (default).",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_false",
        dest="skip_existing",
        help="Disable skipping and attempt rebuild.",
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Force rebuild even if outputs exist or schema config differs.",
    )
    parser.add_argument(
        "--delete-old",
        action="store_true",
        help="DANGEROUS: permanently delete existing outputs instead of archiving.",
    )
    args = parser.parse_args()

    topics = args.topics or DEFAULT_TOPICS
    workspace_root = args.workspace_root.resolve()
    pdf_root = args.pdf_root.resolve()
    report_dir = args.report_dir.resolve()
    config = load_schema_induction_config(PROJECT_ROOT)

    if args.verify_only:
        exit_code = verify_outputs(topics, workspace_root, report_dir)
        raise SystemExit(exit_code)

    schema_mismatches: Dict[str, str] = {}
    for topic in topics:
        workspace = workspace_root / topic
        pdf_dir = pdf_root / topic
        if not pdf_dir.exists():
            raise SystemExit(f"PDF folder not found: {pdf_dir}")
        workspace.mkdir(parents=True, exist_ok=True)
        outputs = collect_workspace_outputs(workspace)

        schema_ok, schema_msg = schema_matches_config(workspace, config)
        if not schema_ok and (workspace / "kg_schema.json").exists():
            schema_mismatches[topic] = schema_msg

        text_dir = workspace / "text"
        corpus_index = workspace / "corpus_index.json"
        has_text = corpus_index.exists() and any(text_dir.glob("*.txt"))
        vector_config = outputs["vector_store"] / "config.json"
        has_vector = vector_config.exists()
        has_schema = outputs["schema"].exists()
        has_edges = outputs["edges"].exists() and outputs["graph_overview"].exists()
        has_graph = outputs["graph"].exists()
        kg_vector_config = outputs["kg_vector_store"] / "config.json"
        has_kg_vector = kg_vector_config.exists()

        if schema_mismatches.get(topic) and not args.force_rebuild:
            if not args.skip_existing:
                raise SystemExit(
                    f"Schema config mismatch for {topic}; use --force-rebuild to override."
                )

        steps_to_run: List[Tuple[str, List[str], List[Path]]] = []
        archive_targets: List[Path] = []
        def maybe_run(label: str, cmd: List[str], outputs_to_archive: Iterable[Path], should_run: bool) -> None:
            if should_run:
                steps_to_run.append((label, cmd, list(outputs_to_archive)))

        force = args.force_rebuild
        skip = args.skip_existing and not force

        maybe_run(
            "extract_text",
            [
                sys.executable,
                str(PROJECT_ROOT / "forge" / "scripts" / "generic_extract_corpus.py"),
                "--pdf-dir",
                str(pdf_dir),
                "--workspace",
                str(workspace),
            ],
            [],
            force or not (skip and has_text),
        )

        maybe_run(
            "text_vector_store",
            [
                sys.executable,
                str(PROJECT_ROOT / "forge" / "scripts" / "generic_build_vector_store.py"),
                "--workspace",
                str(workspace),
                "--model",
                args.model,
                "--embedding-backend",
                args.embedding_backend,
            ],
            [outputs["vector_store"]],
            force or not (skip and has_vector),
        )

        schema_should_run = force or not (skip and has_schema)
        if schema_mismatches.get(topic) and not force:
            schema_should_run = False
            print(f"[forge] Schema config mismatch for {topic}; skipping schema rebuild.")
        if schema_should_run:
            ensure_pydantic_ai_available(config)
        maybe_run(
            "schema",
            [
                sys.executable,
                str(PROJECT_ROOT / "forge" / "agents" / "kg_schema_agent.py"),
                "--workspace",
                str(workspace),
                "--focus-query",
                args.focus_query,
            ],
            [outputs["schema"]],
            schema_should_run,
        )

        edges_should_run = force or not (skip and has_edges)
        if schema_mismatches.get(topic) and not force and not has_edges and edges_should_run:
            raise SystemExit(
                f"Schema config mismatch for {topic}; use --force-rebuild before rebuilding edges."
            )
        maybe_run(
            "kg_edges",
            [
                sys.executable,
                str(PROJECT_ROOT / "forge" / "scripts" / "build_kg_edges.py"),
                "--workspace",
                str(workspace),
                "--schema",
                str(outputs["schema"]),
            ],
            [outputs["edges"], outputs["graph_overview"]],
            edges_should_run,
        )

        graph_should_run = force or not (skip and has_graph)
        maybe_run(
            "graph_store",
            [
                sys.executable,
                str(PROJECT_ROOT / "forge" / "scripts" / "build_graph_store.py"),
                "--edges",
                str(outputs["edges"]),
                "--database",
                str(outputs["graph"]),
            ],
            [outputs["graph"]],
            graph_should_run,
        )

        kg_vector_should_run = force or not (skip and has_kg_vector)
        maybe_run(
            "kg_vector_store",
            [
                sys.executable,
                str(PROJECT_ROOT / "forge" / "scripts" / "build_vector_store.py"),
                "--edges",
                str(outputs["edges"]),
                "--out-dir",
                str(outputs["kg_vector_store"]),
                "--model",
                args.kg_model,
                "--embedding-backend",
                args.kg_embedding_backend,
            ],
            [outputs["kg_vector_store"]],
            kg_vector_should_run,
        )

        if steps_to_run:
            for _, _, archive_list in steps_to_run:
                archive_targets.extend(archive_list)
            if archive_targets:
                archive_dir = archive_outputs(
                    workspace=workspace,
                    report_dir=report_dir,
                    outputs=archive_targets,
                    report_outputs=[],
                    delete_old=args.delete_old,
                )
                if archive_dir:
                    print(f"Archived outputs for {topic} -> {archive_dir}")
        else:
            print(f"[forge] {topic}: all core outputs present; skipping rebuild.")

        for label, cmd, _ in steps_to_run:
            print(f"[forge] {topic}: running {label}")
            run(cmd)

    max_pdfs = args.max_pdfs if args.max_pdfs is not None else args.limit_pdfs
    audit_missing = False
    for topic in topics:
        reports = collect_report_outputs(report_dir, topic, include_combined=False)
        if not (reports["topic_json"].exists() and reports["topic_md"].exists()):
            audit_missing = True
            break
        facts_path = (workspace_root / topic / "facts" / "facts.jsonl")
        if not facts_path.exists():
            audit_missing = True
            break

    audit_should_run = args.force_rebuild or (not args.skip_existing) or audit_missing
    if audit_should_run:
        combined_archived = False
        for topic in topics:
            workspace = workspace_root / topic
            outputs = collect_workspace_outputs(workspace)
            reports = collect_report_outputs(report_dir, topic, include_combined=not combined_archived)
            archive_dir = archive_outputs(
                workspace=workspace,
                report_dir=report_dir,
                outputs=[outputs["facts"]],
                report_outputs=list(reports.values()),
                delete_old=args.delete_old,
            )
            if archive_dir:
                print(f"Archived facts/reports for {topic} -> {archive_dir}")
            if not combined_archived:
                combined_archived = True

        audit_cmd: List[str] = [
            sys.executable,
            str(PROJECT_ROOT / "forge" / "scripts" / "run_structured_audit.py"),
            "--topics",
            *topics,
            "--workspace-root",
            str(workspace_root),
            "--pdf-root",
            str(pdf_root),
            "--report-dir",
            str(report_dir),
        ]
        if max_pdfs:
            audit_cmd.extend(["--max-pdfs", str(max_pdfs)])
        if args.max_pages:
            audit_cmd.extend(["--max-pages", str(args.max_pages)])
        if args.no_ocr:
            audit_cmd.append("--no-ocr")
        run(audit_cmd)
    else:
        print("[forge] Audit reports present; skipping structured audit.")


if __name__ == "__main__":
    main()
