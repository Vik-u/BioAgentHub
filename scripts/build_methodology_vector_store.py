#!/usr/bin/env python3
"""Build vector store over methodology sections."""

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


def load_sections(method_dir: Path) -> List[dict]:
    docs: List[dict] = []
    for json_path in sorted(method_dir.glob("*.json")):
        data = json.loads(json_path.read_text())
        pdf = data.get("pdf_file")
        title = data.get("title") or pdf or json_path.stem
        for section_type in ("experimental_sections", "computational_sections", "results_sections"):
            for idx, section in enumerate(data.get(section_type, [])):
                text = section.get("text", "").strip()
                if len(text) < 200:
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
    parser.add_argument("--method-dir", type=Path, default=Path("KnowledgeGraph/methodology_full"))
    parser.add_argument("--out-dir", type=Path, default=Path("KnowledgeGraph/methodology_vector_store"))
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--no-faiss", action="store_true")
    args = parser.parse_args()

    docs = load_sections(args.method_dir)
    if not docs:
        raise SystemExit("No methodology sections found.")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(args.model)
    embeddings = model.encode([doc["text"] for doc in docs], batch_size=32, show_progress_bar=True).astype("float32")
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
        "embedding_file": "embeddings.npy",
        "metadata_file": meta_path.name,
        "faiss_index_file": faiss_path.name if faiss_path else None,
    }
    (args.out_dir / "config.json").write_text(json.dumps(config, indent=2))
    print(f"Built methodology vector store with {len(docs)} sections")


if __name__ == "__main__":
    main()
