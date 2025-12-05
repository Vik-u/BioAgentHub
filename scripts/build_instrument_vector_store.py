#!/usr/bin/env python3
"""Build FAISS vector store for instrument KG sentences."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

try:
    import faiss
except Exception:  # pragma: no cover
    faiss = None


def load_edges(edge_path: Path) -> List[dict]:
    rows = []
    with edge_path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edges", type=Path, default=Path("InstrumentGraph/kg_edges.jsonl"))
    parser.add_argument("--out-dir", type=Path, default=Path("InstrumentGraph/vector_store"))
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--no-faiss", action="store_true")
    args = parser.parse_args()

    edges = load_edges(args.edges)
    docs = [
        {
            "text": f"{edge['instrument']} {edge['relation']} {edge['value']}. Evidence: {edge['sentence']}",
            "metadata": edge,
        }
        for edge in edges
    ]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(args.model)
    embeddings = model.encode([doc["text"] for doc in docs], batch_size=64, show_progress_bar=True).astype("float32")
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
        "document_count": len(docs),
        "dimension": embeddings.shape[1],
        "faiss_index_file": faiss_path.name if faiss_path else None,
        "metadata_file": meta_path.name,
        "embedding_file": "embeddings.npy",
    }
    (args.out_dir / "config.json").write_text(json.dumps(config, indent=2))
    print(f"Instrument vector store ready with {len(docs)} docs")


if __name__ == "__main__":
    main()
