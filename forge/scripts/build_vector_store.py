#!/usr/bin/env python3
"""Generate a semantic vector store for KG edges using Sentence Transformers."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List

import numpy as np

try:
    import faiss
except Exception:  # pragma: no cover - optional dep
    faiss = None


def load_edges(edge_path: Path) -> List[dict]:
    payloads = []
    with edge_path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payloads.append(json.loads(line))
    return payloads


def build_documents(edges: List[dict]) -> List[dict]:
    docs = []
    for idx, edge in enumerate(edges):
        sentence = edge.get("sentence") or ""
        text = (
            f"{edge['source']} {edge['relation']} {edge['target']}. "
            f"Evidence: {sentence}"
        )
        docs.append(
            {
                "id": idx,
                "text": text,
                "metadata": {
                    "source": edge.get("source"),
                    "relation": edge.get("relation"),
                    "target": edge.get("target"),
                    "paper": edge.get("paper"),
                },
            }
        )
    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--edges",
        type=Path,
        # Legacy: uses archived KnowledgeGraph outputs; canonical uses workspaces/<topic>/ (Forge).
        default=Path("archive/legacy_20260204/KnowledgeGraph/kg_edges.jsonl"),
        help="Path to the JSONL edge file.",
    )
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model identifier (backend-specific).",
    )
    parser.add_argument(
        "--embedding-backend",
        default=os.environ.get("EMBEDDING_BACKEND", "sentence-transformers"),
        help="Embedding backend: sentence-transformers or openai.",
    )
    parser.add_argument("--batch-size", type=int, default=64, help="Embedding batch size.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        # Legacy: uses archived KnowledgeGraph outputs; canonical uses workspaces/<topic>/ (Forge).
        default=Path("archive/legacy_20260204/KnowledgeGraph/vector_store"),
        help="Directory for embeddings and metadata.",
    )
    parser.add_argument(
        "--no-faiss",
        action="store_true",
        help="Skip building a FAISS index even if faiss is available.",
    )
    args = parser.parse_args()

    if not args.edges.exists():
        raise SystemExit(f"Edge file not found: {args.edges}")

    docs = build_documents(load_edges(args.edges))
    if not docs:
        raise SystemExit("No documents to embed.")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    from fabric.services.embedding_backends import (  # noqa: E402
        EmbedderUnavailable,
        embed_in_batches,
        load_embedding_backend,
    )
    embedder = load_embedding_backend(args.embedding_backend, args.model)
    try:
        status = embedder.status()
        if not status.available:
            raise EmbedderUnavailable(status.error or "Embedding backend unavailable.")
    except AttributeError:
        pass
    embeddings = embed_in_batches(embedder, [doc["text"] for doc in docs], batch_size=args.batch_size)
    embeddings = embeddings.astype("float32")

    emb_path = args.out_dir / "embeddings.npy"
    np.save(emb_path, embeddings)

    faiss_index_path = None
    if not args.no_faiss and faiss is not None:
        normed = embeddings.copy()
        faiss.normalize_L2(normed)
        index = faiss.IndexFlatIP(normed.shape[1])
        index.add(normed)
        faiss_index_path = args.out_dir / "index.faiss"
        faiss.write_index(index, str(faiss_index_path))

    meta_path = args.out_dir / "metadata.jsonl"
    with meta_path.open("w", encoding="utf-8") as handle:
        for doc in docs:
            enriched = {
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc["metadata"],
            }
            handle.write(json.dumps(enriched, ensure_ascii=False) + "\n")

    config = {
        "model": args.model,
        "embedding_backend": args.embedding_backend,
        "dimension": embeddings.shape[1],
        "document_count": len(docs),
        "embedding_file": emb_path.name,
        "metadata_file": meta_path.name,
        "faiss_index_file": faiss_index_path.name if faiss_index_path else None,
    }
    (args.out_dir / "config.json").write_text(json.dumps(config, indent=2))
    print(
        f"Vector store ready at {args.out_dir} with {len(docs)} documents "
        f"(dim={embeddings.shape[1]})."
    )


if __name__ == "__main__":
    main()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
