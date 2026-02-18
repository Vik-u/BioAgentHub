#!/usr/bin/env python3
"""
End-to-end builder for a single topic workspace (text + vectors + KG + graph).

Example:
  python scripts/build_topic_full.py --topic petase --pdf-dir data/petase --workspace workspaces/petase
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
import json


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def _ensure_pydantic_ai_available() -> None:
    try:
        import pydantic_ai  # noqa: F401
    except Exception as exc:
        raise SystemExit(
            "PydanticAI backend is required for KG schema induction but is not installed. "
            "Install with: python -m pip install pydantic-ai-slim[openai]==0.0.18"
        ) from exc


def _load_schema_backend(project_root: Path) -> str:
    config_path = project_root / "config" / "llm_config.json"
    if not config_path.exists():
        return ""
    try:
        payload = json.loads(config_path.read_text())
    except json.JSONDecodeError:
        return ""
    return str(payload.get("schema_induction_backend") or "").lower()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", help="Name used for logging only (e.g., petase, 3hp_pand).")
    parser.add_argument("--pdf-dir", type=Path, required=True, help="Folder containing PDFs for this topic.")
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace root to populate.")
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model for text/vector stores.",
    )
    parser.add_argument(
        "--embedding-backend",
        default="sentence-transformers",
        help="Embedding backend for text vectors (sentence-transformers or openai).",
    )
    parser.add_argument(
        "--kg-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model for KG edge vector store.",
    )
    parser.add_argument(
        "--kg-embedding-backend",
        default="sentence-transformers",
        help="Embedding backend for KG edge vectors (sentence-transformers or openai).",
    )
    parser.add_argument(
        "--skip-kg",
        action="store_true",
        help="Skip KG build (text + vector only).",
    )
    parser.add_argument(
        "--with-artifacts",
        action="store_true",
        help="Extract captions/tables artifacts from PDFs.",
    )
    parser.add_argument(
        "--with-facts",
        action="store_true",
        help="Build normalized facts from text/captions/tables.",
    )
    parser.add_argument(
        "--kg-schema",
        type=Path,
        help="Optional KG schema JSON (defaults to <workspace>/kg_schema.json if present).",
    )
    parser.add_argument(
        "--auto-schema",
        action="store_true",
        help="Generate a KG schema with the LLM agent before extracting edges.",
    )
    parser.add_argument(
        "--focus-query",
        default="protein engineering",
        help="Focus query used by the schema agent (default: protein engineering).",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    pdf_dir = args.pdf_dir.resolve()
    topic_label = args.topic or workspace.name
    project_root = Path(__file__).resolve().parents[2]
    print(f"=== Building topic '{topic_label}' from {pdf_dir} into {workspace}")

    # 1) Text/metadata extraction
    run(
        [
            "python",
            "forge/scripts/generic_extract_corpus.py",
            "--pdf-dir",
            str(pdf_dir),
            "--workspace",
            str(workspace),
        ]
    )

    if args.with_artifacts or args.with_facts:
        run(
            [
                "python",
                "forge/scripts/extract_pdf_artifacts.py",
                "--workspace",
                str(workspace),
                "--pdf-dir",
                str(pdf_dir),
            ]
        )
        if args.with_facts:
            run(
                [
                    "python",
                    "forge/scripts/build_structured_facts.py",
                    "--workspace",
                    str(workspace),
                ]
            )

    # 2) Text vector store
    run(
        [
            "python",
            "forge/scripts/generic_build_vector_store.py",
            "--workspace",
            str(workspace),
            "--model",
            args.model,
            "--embedding-backend",
            args.embedding_backend,
        ]
    )

    if args.skip_kg:
        print("KG build skipped by flag; workspace ready.")
        return

    schema_path = args.kg_schema
    if args.auto_schema and schema_path is None:
        if _load_schema_backend(project_root) == "pydantic_ai":
            _ensure_pydantic_ai_available()
        run(
            [
                "python",
                "forge/agents/kg_schema_agent.py",
                "--workspace",
                str(workspace),
                "--focus-query",
                args.focus_query,
            ]
        )
        schema_path = workspace / "kg_schema.json"

    # 3) KG edges + summary
    kg_cmd = [
        "python",
        "forge/scripts/build_kg_edges.py",
        "--workspace",
        str(workspace),
    ]
    if schema_path:
        kg_cmd.extend(["--schema", str(schema_path)])
    run(kg_cmd)

    # 4) Graph DB
    run(
        [
            "python",
            "forge/scripts/build_graph_store.py",
            "--edges",
            str(workspace / "kg_edges.jsonl"),
            "--database",
            str(workspace / "graph.sqlite"),
        ]
    )

    # 5) KG edge vector store (optional but useful for search over edges)
    run(
        [
            "python",
            "forge/scripts/build_vector_store.py",
            "--edges",
            str(workspace / "kg_edges.jsonl"),
            "--out-dir",
            str(workspace / "kg_vector_store"),
            "--model",
            args.kg_model,
            "--embedding-backend",
            args.kg_embedding_backend,
        ]
    )

    print(f"=== Topic '{topic_label}' workspace ready at {workspace}")


if __name__ == "__main__":
    main()
