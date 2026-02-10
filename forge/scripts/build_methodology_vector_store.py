#!/usr/bin/env python3
"""Build vector store over methodology sections."""

from __future__ import annotations

import argparse
import json
import os
import sys
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


def load_sections(method_dir: Path, min_chars: int) -> List[dict]:
    docs: List[dict] = []
    for json_path in sorted(method_dir.glob("*.json")):
        data = json.loads(json_path.read_text())
        pdf = data.get("pdf_file")
        title = data.get("title") or pdf or json_path.stem
        for section_type in ("experimental_sections", "computational_sections", "results_sections"):
            for idx, section in enumerate(data.get(section_type, [])):
                text = section.get("text", "").strip()
                if len(text) < min_chars:
                    continue
                docs.append(
                    {
                        "id": f"{json_path.stem}:{section_type}:{idx}",
                        "section_type": section_type.replace("_sections", ""),
                        "heading": section.get("heading"),
                        "paper": title,
                        "pdf_file": pdf,
                        "text": text,
                    }
                )
    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method-dir", type=Path, required=True, help="Directory with methodology_full JSON files.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Output directory for vector store.")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument(
        "--embedding-backend",
        default=os.environ.get("EMBEDDING_BACKEND", "sentence-transformers"),
        help="Embedding backend: sentence-transformers or openai.",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--min-chars", type=int, default=200, help="Minimum section length to index.")
    parser.add_argument("--no-faiss", action="store_true")
    args = parser.parse_args()

    docs = load_sections(args.method_dir, args.min_chars)
    if not docs:
        raise SystemExit("No methodology sections found.")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    embedder = load_embedding_backend(args.embedding_backend, args.model)
    try:
        status = embedder.status()
        if not status.available:
            raise EmbedderUnavailable(status.error or "Embedding backend unavailable.")
    except AttributeError:
        pass
    embeddings = embed_in_batches(embedder, [doc["text"] for doc in docs], batch_size=args.batch_size).astype("float32")
    np.save(args.out_dir / "embeddings.npy", embeddings)

    meta_path = args.out_dir / "metadata.jsonl"
    with meta_path.open("w", encoding="utf-8") as handle:
        for doc in docs:
            handle.write(json.dumps(doc, ensure_ascii=False) + "\n")

    faiss_path = None
    if not args.no_faiss and faiss is not None:
        normed = embeddings.copy()
        faiss.normalize_L2(normed)
        index = faiss.IndexFlatIP(normed.shape[1])
        index.add(normed)
        faiss_path = args.out_dir / "index.faiss"
        faiss.write_index(index, str(faiss_path))

    config = {
        "model": args.model,
        "embedding_backend": args.embedding_backend,
        "document_count": len(docs),
        "dimension": embeddings.shape[1],
        "embedding_file": "embeddings.npy",
        "metadata_file": meta_path.name,
        "faiss_index_file": faiss_path.name if faiss_path else None,
    }
    (args.out_dir / "config.json").write_text(json.dumps(config, indent=2))
    print(f"Built methodology vector store with {len(docs)} sections")


if __name__ == "__main__":
    main()
