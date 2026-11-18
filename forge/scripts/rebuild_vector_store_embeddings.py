#!/usr/bin/env python3
"""Re-embed an existing vector store from its metadata.jsonl."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import numpy as np

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover
    faiss = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fabric.services.embedding_backends import (  # noqa: E402
    EmbedderUnavailable,
    embed_in_batches,
    load_embedding_backend,
)


def load_documents(meta_path: Path) -> List[dict]:
    docs = []
    with meta_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))
    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace that already has a vector store.")
    parser.add_argument("--backend", default=None, help="Embedding backend: sentence-transformers or openai.")
    parser.add_argument("--model", default=None, help="Embedding model identifier.")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--no-faiss", action="store_true", help="Skip rebuilding FAISS index.")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    vector_dir = workspace / "vector_store"
    meta_path = vector_dir / "metadata.jsonl"
    if not meta_path.exists():
        raise SystemExit("metadata.jsonl not found in the vector store.")

    config_path = vector_dir / "config.json"
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    backend = args.backend or config.get("embedding_backend") or "sentence-transformers"
    model = args.model or config.get("model")
    if not model:
        raise SystemExit("Embedding model is not defined in config or --model.")

    docs = load_documents(meta_path)
    texts = [doc.get("text", "") for doc in docs]

    embedder = load_embedding_backend(backend, model)
    try:
        embeddings = embed_in_batches(embedder, texts, batch_size=args.batch_size)
    except EmbedderUnavailable as exc:
        raise SystemExit(str(exc))

    emb_path = vector_dir / "embeddings.npy"
    np.save(emb_path, embeddings.astype("float32"))

    faiss_path = None
    if not args.no_faiss and faiss is not None:
        normed = embeddings.copy()
        faiss.normalize_L2(normed)
        index = faiss.IndexFlatIP(normed.shape[1])
        index.add(normed)
        faiss_path = vector_dir / "index.faiss"
        faiss.write_index(index, str(faiss_path))

    provenance = {
        "backend": backend,
        "model": model,
        "dimension": int(embeddings.shape[1]) if embeddings.size else 0,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    config.update({
        "embedding_backend": backend,
        "model": model,
        "dimension": int(embeddings.shape[1]) if embeddings.size else 0,
        "document_count": len(docs),
        "embedding_file": emb_path.name,
        "metadata_file": meta_path.name,
        "faiss_index_file": faiss_path.name if faiss_path else None,
        "provenance": provenance,
    })
    config_path.write_text(json.dumps(config, indent=2))

    print(f"Rebuilt embeddings for {len(docs)} chunks (dim={embeddings.shape[1]}).")


if __name__ == "__main__":
    main()
